# Análisis Arquitectónico — Food Store Backend
> Generado: 2026-05-08

---

## Resumen Ejecutivo

Se identificaron **14 inconsistencias** en el backend actual comparado con los changes futuros definidos en `docs/CHANGES.md`. La severidad general es **media-alta**: el núcleo de infraestructura está bien construido (modelos, UoW, BaseRepository, error middleware), pero hay gaps críticos que bloquearán los primeros changes de features (auth, productos, pedidos, pagos). Los problemas más graves son: (1) ningún router de feature está registrado en `main.py`, (2) el hashing usa Argon2 en `core/security.py` pero los modelos usan bcrypt — una contradicción directa que rompe auth-login, y (3) el modelo `Pedido` carece del campo `direccion_snapshot` requerido por el change `orders-fsm-backend`. Se recomienda corregir las inconsistencias de severidad alta antes de iniciar cualquier change de EPIC 01 en adelante.

---

## Inconsistencias por Categoría

### 1. Modelos SQLModel vs ERD v5

#### 1.1 — Falta `UsuarioRol` (tabla N:M): ERD v5 define relación N:M entre usuarios y roles

**Qué está mal**: El change `backend-postgres-alembic-seed` describe en su sección "Dominio 1" la existencia de una tabla `UsuarioRol`. El modelo actual implementa `Usuario.rol_id` como FK directa (relación 1:N). El change `rbac-roles-management` dice explícitamente: _"Relación N:M Usuario-Rol con restricción UNIQUE compuesta"_.

**Por qué rompe**: El change `rbac-roles-management` espera poder asignar múltiples roles a un usuario. Con el modelo actual (un solo `rol_id`), el endpoint `PUT /api/admin/users/:id/role` no puede implementar múltiples roles ni la validación "ADMIN no puede quitarse el rol ADMIN a sí mismo si es el último admin" de forma correcta.

**Cómo corregirlo**: Crear modelo `UsuarioRol` y migración Alembic correspondiente:
```python
class UsuarioRol(SQLModel, table=True):
    __tablename__ = "usuario_rol"
    usuario_id: int = Field(foreign_key="usuarios.id", primary_key=True)
    rol_id: int = Field(foreign_key="roles.id", primary_key=True)
    asignado_en: datetime = Field(default_factory=datetime.utcnow)
```
Y mantener o eliminar `Usuario.rol_id` según decisión de compatibilidad hacia atrás. Si se mantiene `rol_id` para compatibilidad con el seed actual, documentarlo como deprecated.

---

#### 1.2 — `Pedido` no tiene `direccion_snapshot`

**Qué está mal**: El change `orders-fsm-backend` describe explícitamente el patrón de snapshots: _"Snapshot pattern: guardar precio, nombre, **dirección** al crear pedido"_. El modelo `Pedido` actual solo tiene `direccion_entrega_id` (FK viva), sin snapshot de la dirección al momento del pedido.

**Por qué rompe**: Si el usuario edita o elimina su dirección después de crear el pedido, el historial del pedido pierde la dirección real de entrega. El change `orders-api-endpoints` requiere retornar en el detalle: _"dirección de entrega (snapshot)"_.

**Cómo corregirlo**: Agregar campos de snapshot al modelo `Pedido`:
```python
# En Pedido, agregar:
direccion_snapshot: Optional[str] = None  # JSON con alias, linea1, ciudad, cp
```
Y crear migración Alembic para la nueva columna.

---

#### 1.3 — `DetallePedido.ingredientes_excluidos` usa `str` en lugar de `JSON`

**Qué está mal**: El campo `ingredientes_excluidos` está declarado como `Optional[str]` con comentario `# JSON array as string`. Tanto el modelo SQLModel como la migración Alembic usan `sa.String()` en lugar de `sa.JSON()` o `JSONB`.

**Por qué rompe**: El change `orders-fsm-backend` necesita procesar los ingredientes excluidos como array estructurado. El change `frontend-orders-detail-ui` necesita mostrar _"ingredientes excluidos"_ formateados por ítem. Con un `str`, el servicio tendrá que hacer `json.loads()` manualmente con riesgo de errores de deserialización y sin validación de tipos.

**Cómo corregirlo**: Cambiar a tipo JSON nativo en la migración:
```python
sa.Column('ingredientes_excluidos', postgresql.JSONB(), nullable=True)
```
Y en el modelo:
```python
from sqlalchemy import JSON
ingredientes_excluidos: Optional[list[int]] = Field(default=None, sa_column=Column(JSON))
```

---

#### 1.4 — `Usuario` no tiene campo `telefono`

**Qué está mal**: El change `backend-user-profile-endpoints` describe que `PUT /api/v1/perfil` permite actualizar _"nombre, teléfono"_. El modelo `Usuario` actual no tiene campo `telefono`.

**Por qué rompe**: El change `frontend-user-profile-ui` muestra en el perfil: _"nombre, email, teléfono, fecha de registro"_. Sin el campo, el endpoint de perfil no puede almacenarlo.

**Cómo corregirlo**: Agregar campo al modelo y crear migración:
```python
telefono: Optional[str] = Field(default=None, max_length=20)
```

---

#### 1.5 — `Usuario` no tiene campo `ultimo_login`

**Qué está mal**: El change `frontend-user-profile-ui` dice _"Mostrar última vez logueo"_. No existe campo `ultimo_login` en el modelo.

**Por qué rompe**: Sin el campo, el endpoint `GET /api/v1/perfil` no puede retornar la fecha del último login.

**Cómo corregirlo**: Agregar campo opcional:
```python
ultimo_login: Optional[datetime] = None
```
Y actualizar el servicio de login para setear `ultimo_login = datetime.utcnow()` en cada login exitoso.

---

### 2. Unit of Work y Repositorios

#### 2.1 — `BaseRepository` no tiene método `find_by` para búsquedas filtradas

**Qué está mal**: El `BaseRepository` tiene solo `get_by_id()`, `list_all()`, `count()`, `create()`, `update()`, `soft_delete()`, `hard_delete()`. No tiene un método genérico de búsqueda por campo(s) o filtro arbitrario más allá de `execute_query()` que requiere construir la query completa externamente.

**Por qué rompe**: Múltiples changes necesitan búsquedas específicas:
- `auth-login`: buscar usuario por email (`WHERE email = $1`)
- `auth-token-refresh`: buscar refresh token por valor + verificar no revocado
- `products-catalog-public`: filtrar por categoría, nombre ILIKE, excluir alérgenos
- `orders-api-endpoints`: filtrar pedidos por usuario_id, estado, fecha

Sin un método `find_by()` o `filter()`, cada servicio tendrá que llamar `execute_query()` construyendo la query desde cero, duplicando lógica de soft-delete filtering.

**Cómo corregirlo**: Agregar método de búsqueda por campo único (lo más crítico):
```python
async def get_by_field(self, field: str, value: Any) -> Optional[T]:
    """Get first entity matching field=value, respecting soft-delete."""
    query = select(self.model).where(getattr(self.model, field) == value)
    if hasattr(self.model, "eliminado_en"):
        query = query.where(self.model.eliminado_en.is_(None))
    result = await self.session.execute(query)
    return result.scalars().first()

async def list_filtered(self, filters: dict, skip: int = 0, limit: int = 100) -> list[T]:
    """List entities matching all filters, respecting soft-delete."""
    query = select(self.model)
    if hasattr(self.model, "eliminado_en"):
        query = query.where(self.model.eliminado_en.is_(None))
    for field, value in filters.items():
        query = query.where(getattr(self.model, field) == value)
    return (await self.session.execute(query.offset(skip).limit(limit))).scalars().all()
```

---

#### 2.2 — `UnitOfWork` no tiene repositorio para `UsuarioRol` (si se crea la tabla N:M)

**Qué está mal**: Si se implementa la corrección 1.1 (tabla `UsuarioRol`), el `UnitOfWork` actual no expone `uow.usuario_roles` como propiedad.

**Por qué rompe**: El change `rbac-roles-management` necesita crear/eliminar entradas en `usuario_rol` dentro del mismo contexto transaccional que modifica `usuarios`.

**Cómo corregirlo**: Una vez creado el modelo `UsuarioRol`, agregar propiedad al UoW:
```python
@property
def usuario_roles(self) -> BaseRepository[UsuarioRol]:
    if "usuario_roles" not in self._repositories:
        self._repositories["usuario_roles"] = BaseRepository(self.session, UsuarioRol)
    return self._repositories["usuario_roles"]
```

---

#### 2.3 — `get_current_user()` usa `async with uow` implícitamente cerrando la transacción antes de que el endpoint la use

**Qué está mal**: En `infrastructure/dependencies.py`, `get_current_user()` hace:
```python
async with uow:
    user = await uow.usuarios.get_by_id(user_id)
```
El `async with uow` llama `__aexit__` que hace `commit()` y libera la sesión. Si el endpoint que usa `get_current_user()` como dependencia intenta reutilizar la misma sesión para sus operaciones (a través del mismo `uow` inyectado), la sesión ya fue cerrada.

**Por qué rompe**: En rutas como `POST /api/v1/pedidos` que necesitan tanto autenticar al usuario (`get_current_user`) como crear un pedido en la misma transacción, el UoW se habría consumido en la dependencia de autenticación. Los cambios del pedido irían en un UoW diferente, perdiendo atomicidad.

**Cómo corregirlo**: `get_current_user` no debería abrir el contexto `async with uow`. Debe hacer la consulta directamente sin commitear:
```python
async def get_current_user(
    payload: dict[str, Any] = Depends(verify_token_dependency),
    uow: UnitOfWork = Depends(get_uow),
) -> Usuario:
    user_id = int(payload.get("sub"))
    # No usar "async with uow" aquí — solo consultar
    user = await uow.usuarios.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found", ...)
    if user.eliminado_en is not None:
        raise HTTPException(status_code=403, detail="User account has been deleted")
    return user
```

---

### 3. Auth y JWT

#### 3.1 — Contradicción en algoritmo de hashing: Argon2 vs bcrypt

**Qué está mal**: `core/security.py` usa `CryptContext(schemes=["argon2"])` (Argon2). El modelo `Usuario` tiene un método `hash_password()` que usa `CryptContext(schemes=["bcrypt"])` instanciado directamente en `core/models.py`. El change `auth-login` especifica: _"bcrypt (cost factor >= 10)"_ y el `core/config.py` tiene la variable `bcrypt_cost`.

**Por qué rompe**: Si el seed crea el admin usando `Usuario.hash_password()` (bcrypt) y el login verifica con `core/security.verify_password()` (Argon2), la verificación siempre fallará para usuarios creados con bcrypt. Las pruebas del change `auth-login` fallarán desde el primer intento.

**Cómo corregirlo**: Unificar en un solo algoritmo. Dado que CHANGES.md, AGENTS.md y config.py referencian bcrypt, la corrección es cambiar `core/security.py`:
```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```
Y eliminar el `pwd_context` duplicado de `core/models.py`, delegando todo el hashing a `core/security.py`.

---

#### 3.2 — `create_refresh_token()` no lleva `sub` (user_id) en el payload

**Qué está mal**: `create_refresh_token()` en `core/security.py` genera un token JWT sin campo `sub`. El payload solo tiene `type`, `jti`, `exp`, `iat`, `nbf`, `iss`, `aud`.

**Por qué rompe**: El change `auth-token-refresh` describe el flujo: _"Validar que el token existe en BD, no esté expirado, no esté revocado"_. El lookup en BD se hace por el valor del token almacenado en la tabla `refresh_tokens`. Sin `sub`, si el servicio de refresh intenta extraer el `user_id` del payload JWT del refresh token (en lugar de hacer la consulta a BD), obtendrá `None`. Además, el replay attack detection necesita saber a qué usuario pertenece el token revocado para _"revocar TODOS los tokens del usuario"_.

**Cómo corregirlo**: Agregar `sub` al payload del refresh token:
```python
def create_refresh_token(user_id: int) -> str:
    to_encode = {
        "type": "refresh",
        "sub": str(user_id),  # Agregar user_id
        "jti": str(uuid.uuid4()),
    }
    # ... resto del código
```

---

#### 3.3 — `verify_token()` no distingue access token vs refresh token

**Qué está mal**: `verify_token()` es una función única que decodifica cualquier JWT. No hay parámetro `is_refresh` ni validación del claim `type`. Un refresh token podría usarse como access token en cualquier endpoint protegido.

**Por qué rompe**: El change `auth-token-refresh` requiere que el endpoint `POST /api/v1/auth/refresh` acepte solo refresh tokens. El endpoint `POST /api/v1/auth/logout` también espera un refresh token. Si `verify_token()` se llama igual en todos lados, no hay forma de prevenir que un refresh token sea presentado como access token o viceversa.

**Cómo corregirlo**: Agregar validación del claim `type`:
```python
def verify_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    payload = jwt.decode(...)  # igual que ahora
    token_type = payload.get("type", "access")
    if token_type != expected_type:
        raise credentials_exception
    return payload
```

---

### 4. Estructura de Rutas

#### 4.1 — `main.py` no incluye ningún router de feature

**Qué está mal**: El `main.py` solo tiene health check (`/health`) y root (`/`). Tiene un bloque de comentarios con los imports futuros pero ninguno está activo:
```python
# Future routers will be included here:
# from api.v1 import auth, products, orders, payments
# app.include_router(auth.router, prefix="/api/v1")
```

Además, la estructura de importación comentada es `from api.v1 import auth` — pero la estructura real del proyecto es feature-first (`backend/auth/`, `backend/productos/`), no `backend/api/v1/`.

**Por qué rompe**: Cada change de feature (auth-registration, auth-login, products-crud-core, etc.) necesita que su router sea registrado en `main.py`. Sin esto, los endpoints no existen. Adicionalmente, el path de importación comentado no coincide con la estructura real del proyecto.

**Cómo corregirlo**: El patrón correcto de import para la estructura feature-first:
```python
# En main.py, cuando se creen los routers:
from auth.router import router as auth_router
from productos.router import router as productos_router
from pedidos.router import router as pedidos_router
from pagos.router import router as pagos_router

app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
app.include_router(productos_router, prefix="/api/v1", tags=["Productos"])
app.include_router(pedidos_router, prefix="/api/v1", tags=["Pedidos"])
app.include_router(pagos_router, prefix="/api/v1", tags=["Pagos"])
```

---

#### 4.2 — Las carpetas de features existen en el directorio pero están vacías

**Qué está mal**: Las carpetas `backend/auth/`, `backend/productos/`, `backend/pedidos/`, `backend/pagos/`, `backend/categorias/`, `backend/ingredientes/`, `backend/usuarios/`, `backend/direcciones/`, `backend/admin/`, `backend/refresh_tokens/` existen (según la estructura del change `infrastructure-repo-setup`) pero no contienen archivos `.py`.

**Por qué rompe**: Los changes de EPIC 01 en adelante asumen que pueden crear `router.py`, `service.py`, `repository.py`, `schemas.py` en estas carpetas. Si las carpetas no tienen `__init__.py`, Python no las reconocerá como paquetes y los imports fallarán.

**Cómo corregirlo**: Verificar que cada carpeta de feature tenga al menos un `__init__.py` vacío antes de comenzar a implementar los changes de features. Esto es una precondición para todos los EPIC 01+.

---

### 5. Migraciones Alembic

#### 5.1 — Migración 001 crea 15 tablas pero ERD v5 tiene 16 (falta `usuario_rol`)

**Qué está mal**: La migración `001_initial_schema.py` crea 15 tablas (roles, estados_pedido, formas_pago, usuarios, refresh_tokens, direcciones_entrega, categorias, productos, ingredientes, producto_categoria, producto_ingrediente, pedidos, detalle_pedido, historial_estado_pedido, pagos). El change `backend-postgres-alembic-seed` lista 16 tablas incluyendo `UsuarioRol`.

**Por qué rompe**: El change `rbac-roles-management` necesita la tabla `usuario_rol`. Sin migración, el startup de la app fallará con un error de tabla inexistente cuando se intente acceder a `usuario_rol`.

**Cómo corregirlo**: Crear una migración 002 que agregue la tabla `usuario_rol` y los campos faltantes (`telefono`, `ultimo_login`, `direccion_snapshot`).

---

#### 5.2 — Alembic usa URL síncrona en `alembic.ini` pero el engine es async

**Qué está mal**: `alembic.ini` define:
```
sqlalchemy.url = postgresql+psycopg://postgres:postgres@localhost:5433/foodstore_db
```
El engine en `core/database.py` usa `create_async_engine`. Alembic necesita configuración especial para trabajar con engines async.

**Por qué rompe**: Cuando se ejecute `alembic upgrade head` usando la URL de `alembic.ini`, usará el driver síncrono `psycopg` (sin `asyncpg` ni el modo async). Si `env.py` no está configurado correctamente para async, las migraciones pueden ejecutarse pero con un engine diferente al que usa la app en producción. Esto puede causar diferencias de esquema entre lo que Alembic ve y lo que el app usa.

**Cómo corregirlo**: Verificar que `backend/alembic/env.py` use `run_async_migrations()` con el engine async de la aplicación, no la URL de `alembic.ini`. El `env.py` debería importar `settings.database_url` y el engine definido en `core/database.py`.

---

### 6. MercadoPago

#### 6.1 — Módulo `pagos/` no existe: el change `payments-mercadopago-integration-backend` tiene prerequisitos no implementados

**Qué está mal**: La carpeta `backend/pagos/` existe (según estructura del repo) pero no contiene código. El change `payments-mercadopago-integration-backend` depende de `orders-fsm-backend`, que a su vez depende de `backend-patterns-base-repository-uow` y `products-crud-core`. Ningún change de EPIC 05-09 está implementado.

**Por qué rompe**: Este no es en sí un error arquitectónico sino un recordatorio de que el módulo de pagos no puede ser implementado hasta que toda la cadena de dependencias esté completa. Documentado como "no implementado" por diseño.

---

#### 6.2 — `config.py` tiene `mercadopago_access_token` pero el change describe `MP_ACCESS_TOKEN` como nombre de variable

**Qué está mal**: `core/config.py` define las variables MercadoPago como:
```python
mercadopago_access_token: str = Field(default="", alias="MERCADOPAGO_ACCESS_TOKEN")
mercadopago_public_key: str = Field(default="", alias="MERCADOPAGO_PUBLIC_KEY")
```
El change `payments-mercadopago-integration-backend` y `docs/CHANGES.md` (sección Notas Importantes) referencia las variables como `MP_ACCESS_TOKEN` y `MP_PUBLIC_KEY`.

**Por qué rompe**: El `.env.example` (si existe) y la documentación para los integradores del change de pagos usarán `MP_ACCESS_TOKEN`. Si el `.env` del desarrollador tiene esas variables con el nombre corto y `config.py` busca `MERCADOPAGO_ACCESS_TOKEN`, las credenciales no se cargarán (quedarán en string vacío `""`), haciendo fallar silenciosamente la integración MP.

**Cómo corregirlo**: Unificar. Elegir uno de los dos naming conventions y documentarlo en `.env.example`. La opción más segura es agregar ambos aliases:
```python
mercadopago_access_token: str = Field(default="", validation_alias=AliasChoices("MP_ACCESS_TOKEN", "MERCADOPAGO_ACCESS_TOKEN"))
```

---

## Prioridad de Corrección

| Severidad | Inconsistencia | Change Afectado | Esfuerzo |
|-----------|---------------|-----------------|----------|
| Alta | 3.1 — Argon2 vs bcrypt: contradicción de hashing | `auth-login`, `auth-registration` | Bajo (cambiar 1 línea en security.py, unificar pwd_context) |
| Alta | 2.3 — `get_current_user` consume el UoW en la dependencia | Todos los endpoints protegidos con operaciones de escritura | Bajo (quitar `async with uow`) |
| Alta | 4.1 — `main.py` sin routers, path de import incorrecto | Todos los EPIC 01+ | Bajo (actualizar comentarios ahora; cada change agrega su router) |
| Alta | 3.2 — `create_refresh_token()` sin campo `sub` | `auth-token-refresh`, `auth-logout` | Bajo (agregar parámetro user_id) |
| Alta | 3.3 — `verify_token()` no distingue tipo de token | `auth-token-refresh`, `auth-logout` | Bajo (agregar param expected_type) |
| Alta | 1.1 — Falta tabla `UsuarioRol` (N:M) | `rbac-roles-management` | Medio (nuevo modelo + migración 002) |
| Alta | 5.1 — Migración crea 15 tablas, ERD v5 tiene 16 | `rbac-roles-management` | Medio (nueva migración 002) |
| Media | 2.1 — `BaseRepository` sin método `find_by` / `filter` | `auth-login`, `products-catalog-public`, `orders-api-endpoints` | Medio (agregar 2 métodos al BaseRepository) |
| Media | 1.2 — `Pedido` sin `direccion_snapshot` | `orders-fsm-backend`, `orders-api-endpoints` | Medio (campo nuevo + migración) |
| Media | 1.4 — `Usuario` sin campo `telefono` | `backend-user-profile-endpoints` | Bajo (campo nuevo + migración) |
| Media | 1.5 — `Usuario` sin campo `ultimo_login` | `frontend-user-profile-ui` | Bajo (campo nuevo + migración) |
| Media | 5.2 — Alembic con URL síncrona vs engine async | Toda ejecución de `alembic upgrade` | Medio (verificar env.py) |
| Media | 6.2 — Nombres de variables MP inconsistentes | `payments-mercadopago-integration-backend` | Bajo (actualizar alias en config.py) |
| Baja | 1.3 — `ingredientes_excluidos` como str en vez de JSON | `orders-fsm-backend`, `frontend-orders-detail-ui` | Medio (cambio de tipo + migración) |
| Baja | 2.2 — UoW sin repositorio `usuario_roles` | `rbac-roles-management` | Bajo (agregar propiedad al UoW) |
| Baja | 4.2 — Carpetas de features sin `__init__.py` | Todos los changes de features | Bajo (crear archivos vacíos) |

---

## Cambios Recomendados (con código)

### Fix 1 — Unificar hashing en bcrypt (CRÍTICO — bloquea auth-login)

**Archivo**: `backend/core/security.py`, líneas 22-25

Cambiar:
```python
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)
```

A:
```python
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)
```

**Archivo**: `backend/core/models.py` — eliminar el `pwd_context` local y delegarle a `core.security`:
```python
# Eliminar estas líneas de models.py:
# from passlib.context import CryptContext
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Reemplazar el método hash_password:
@staticmethod
def hash_password(password: str) -> str:
    from core.security import hash_password
    return hash_password(password)
```

---

### Fix 2 — Corregir `get_current_user` para no consumir la transacción (CRÍTICO)

**Archivo**: `backend/infrastructure/dependencies.py`, líneas 63-100

Cambiar el bloque:
```python
async with uow:
    user = await uow.usuarios.get_by_id(user_id)
```

A:
```python
# Sin context manager — solo consultar, no commitear
user = await uow.usuarios.get_by_id(user_id)
```

---

### Fix 3 — Agregar `sub` a `create_refresh_token` (CRÍTICO — bloquea auth-token-refresh)

**Archivo**: `backend/core/security.py`

```python
def create_refresh_token(user_id: int) -> str:
    """
    Create a refresh token for a specific user.
    
    Args:
        user_id: ID of the user this token belongs to
    """
    jti = str(uuid.uuid4())
    
    to_encode = {
        "type": "refresh",
        "sub": str(user_id),   # AGREGAR user_id
        "jti": jti,
    }
    
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(UTC),
        "nbf": datetime.now(UTC),
        "iss": "foodstore-api",
        "aud": "foodstore-client",
    })
    
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
```

---

### Fix 4 — Agregar validación de tipo en `verify_token` (CRÍTICO — bloquea auth-token-refresh)

**Archivo**: `backend/core/security.py`

```python
def verify_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """
    Verify and decode a JWT token, validating its type.
    
    Args:
        token: JWT token string
        expected_type: "access" or "refresh"
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            audience="foodstore-client",
            issuer="foodstore-api",
        )
        
        # Validate token type
        token_type = payload.get("type", "access")
        if token_type != expected_type:
            raise credentials_exception
            
        return payload
    except JWTError as e:
        print(f"JWT verification failed: {e}")
        raise credentials_exception
```

---

### Fix 5 — Agregar `find_by` al BaseRepository (ALTA PRIORIDAD — bloquea auth-login)

**Archivo**: `backend/infrastructure/repositories/base_repository.py`

Agregar al final de la clase `BaseRepository`:
```python
async def get_by_field(self, field: str, value: Any) -> Optional[T]:
    """
    Get first entity matching a single field value, respecting soft-delete.
    
    Args:
        field: Attribute name on the model (e.g., "email", "token")
        value: Value to match
        
    Returns:
        First matching entity or None
        
    Example:
        user = await uow.usuarios.get_by_field("email", "user@example.com")
    """
    query = select(self.model).where(getattr(self.model, field) == value)
    
    if hasattr(self.model, "eliminado_en"):
        query = query.where(self.model.eliminado_en.is_(None))
    
    result = await self.session.execute(query)
    return result.scalars().first()

async def list_by_field(
    self, field: str, value: Any, skip: int = 0, limit: int = 100
) -> list[T]:
    """
    List all entities matching a single field value, respecting soft-delete.
    
    Args:
        field: Attribute name on the model
        value: Value to match
        skip: Offset for pagination
        limit: Max results
        
    Returns:
        List of matching entities
    """
    limit = min(limit, 1000)
    
    query = (
        select(self.model)
        .where(getattr(self.model, field) == value)
        .offset(skip)
        .limit(limit)
    )
    
    if hasattr(self.model, "eliminado_en"):
        query = query.where(self.model.eliminado_en.is_(None))
    
    result = await self.session.execute(query)
    return result.scalars().all()
```

---

### Fix 6 — Migración 002: agregar tablas y campos faltantes

Crear `backend/alembic/versions/002_add_missing_fields.py`:

```python
"""Add missing fields: usuario_rol table, direccion_snapshot, telefono, ultimo_login

Revision ID: 002_add_missing_fields
Revises: 001_initial_schema
Create Date: 2026-05-08
"""
from alembic import op
import sqlalchemy as sa

revision = '002_add_missing_fields'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create usuario_rol N:M table
    op.create_table(
        'usuario_rol',
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('rol_id', sa.Integer(), nullable=False),
        sa.Column('asignado_en', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rol_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('usuario_id', 'rol_id'),
    )

    # Add telefono and ultimo_login to usuarios
    op.add_column('usuarios', sa.Column('telefono', sa.String(length=20), nullable=True))
    op.add_column('usuarios', sa.Column('ultimo_login', sa.DateTime(), nullable=True))

    # Add direccion_snapshot to pedidos
    op.add_column('pedidos', sa.Column('direccion_snapshot', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('pedidos', 'direccion_snapshot')
    op.drop_column('usuarios', 'ultimo_login')
    op.drop_column('usuarios', 'telefono')
    op.drop_table('usuario_rol')
```

---

## Notas sobre Estado de Implementación de Features

Los siguientes módulos de feature están **no implementados** (carpetas vacías sin código). Esto es esperado según el estado del proyecto (changes pendientes), no son errores arquitectónicos:

| Módulo | Change Responsable | Estado |
|--------|--------------------|--------|
| `backend/auth/` | `auth-registration`, `auth-login`, `auth-token-refresh`, `auth-logout` | No implementado |
| `backend/usuarios/` | `backend-user-profile-endpoints` | No implementado |
| `backend/categorias/` | `categories-crud-hierarchical` | No implementado |
| `backend/ingredientes/` | `ingredients-crud-allergens` | No implementado |
| `backend/productos/` | `products-crud-core`, `products-catalog-public` | No implementado |
| `backend/pedidos/` | `orders-fsm-backend`, `orders-api-endpoints` | No implementado |
| `backend/pagos/` | `payments-mercadopago-integration-backend` | No implementado |
| `backend/direcciones/` | `addresses-crud-by-user` | No implementado |
| `backend/admin/` | `admin-dashboard-metrics` | No implementado |
| `backend/refresh_tokens/` | Integrado en `auth-token-refresh` | No implementado |

El orden correcto para implementarlos respeta las dependencias definidas en CHANGES.md: auth → RBAC → categorias/ingredientes → productos → direcciones → pedidos → pagos → admin.

---

*Análisis realizado sobre los archivos: `backend/core/models.py`, `backend/core/database.py`, `backend/core/security.py`, `backend/core/config.py`, `backend/infrastructure/uow.py`, `backend/infrastructure/dependencies.py`, `backend/infrastructure/error_middleware.py`, `backend/infrastructure/repositories/base_repository.py`, `backend/main.py`, `backend/alembic/versions/001_initial_schema.py`, `backend/scripts/seed.py`, `backend/alembic.ini`, `docs/CHANGES.md`.*
