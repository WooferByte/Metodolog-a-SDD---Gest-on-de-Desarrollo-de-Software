# Food Store — Mapa Completo de Changes (SDD)

> **Documento de referencia**: Define todos los changes necesarios para desarrollar Food Store de principio a fin en el contexto de Spec-Driven Development (SDD).
> 
> **Última actualización**: 21 de abril de 2026
> **Versión especificación**: 5.0 (ERD v5, Feature-First, SDD)

---

## Introducción

Este documento lista **todos los changes** que necesita Food Store para completarse. Cada change está identificado por:
- **Nombre** (kebab-case): identificador único
- **Funcionalidad**: qué cubre
- **Historias de usuario**: QUÉ implementa
- **Dependencias**: de qué otros changes depende y POR QUÉ

El orden sugerido respeta el flujo de dependencias: un change solo puede implementarse cuando todas sus dependencias están archivadas.

---

## EPIC 00 — Infraestructura y Setup (Sprint 0)

### ✅ change: `infrastructure-repo-setup`
**Funcionalidad**: Inicialización del repositorio Git, estructura de carpetas monorepo, configuración de herramientas base.

**Historias**: US-000

**Dependencias**: Ninguna (primer change)

**Descripción**: 
- Crear estructura `/backend` con feature-first (auth/, usuarios/, productos/, categorias/, ingredientes/, pedidos/, pagos/, direcciones/, admin/, refreshtokens/)
- Crear estructura `/frontend` con Feature-Sliced Design (app/, pages/, widgets/, features/, entities/, shared/)
- Configurar `.gitignore`, `.env.example`, `README.md`
- Inicializar git con commits progresivos
- Stack: Python + React + TypeScript

---

### ✅ change: `backend-fastapi-core-setup`
**Funcionalidad**: Configuración del backend FastAPI, dependencias core, estructura base de carpetas.

**Historias**: US-000a

**Dependencias**: `infrastructure-repo-setup`

**Descripción**:
- Setup FastAPI con uvicorn
- Instalar dependencias: FastAPI, SQLModel, Alembic, Passlib[bcrypt], python-jose, slowapi, mercadopago, httpx, pydantic[email-validator]
- Crear `main.py` con CORS middleware y rate limiting
- Crear `core/config.py` (lectura de variables de entorno)
- Crear `core/database.py` (engine y session factory SQLAlchemy)
- Crear `core/security.py` (hashing JWT)
- Swagger UI en `/docs`, ReDoc en `/redoc`

---

### ⏳ change: `backend-dev-infrastructure`
**Funcionalidad**: Infraestructura de desarrollo (Docker Compose, driver psycopg compatible, seed idempotente).

**Historias**: US-000f

**Dependencias**: `backend-fastapi-core-setup`

**Descripción**:
- Crear `docker-compose.yml` con PostgreSQL 16 Alpine, health checks, volumen persistente
- Actualizar `requirements.txt`: reemplazar `asyncpg + psycopg2-binary` con `psycopg[binary]==3.1.17` (Windows compatible)
- Crear `backend/scripts/seed.py` idempotente: 4 Roles, 6 EstadoPedido, 3 FormaPago, 1 admin user
- Actualizar `.env.example` con nuevas variables: DATABASE_URL, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
- Actualizar README.md con instrucciones: "Getting Started" (Docker option + native PostgreSQL option)

---

### ✅ change: `backend-postgres-alembic-seed`
**Funcionalidad**: Base de datos PostgreSQL, migraciones Alembic, seed data obligatorio.

**Historias**: US-000b

**Dependencias**: `backend-fastapi-core-setup`

**Descripción**:
- Conectar PostgreSQL con `DATABASE_URL`
- Crear migrations Alembic para todas las tablas ERD v5:
  - Dominio 1: Usuario, Rol, UsuarioRol, RefreshToken, DireccionEntrega
  - Dominio 2: Categoria, Producto, Ingrediente, ProductoCategoria, ProductoIngrediente, FormaPago
  - Dominio 3: EstadoPedido, Pedido, DetallePedido, HistorialEstadoPedido, Pago
- Implementar soft-delete (`eliminado_en` para entidades, `revoked_at` para RefreshToken)
- Crear script seed idempotente:
  - 4 Roles: ADMIN, STOCK, PEDIDOS, CLIENT
  - 6 EstadoPedido: PENDIENTE, CONFIRMADO, EN_PREPARACIÓN, EN_CAMINO, ENTREGADO, CANCELADO
  - 3 FormaPago: MERCADOPAGO, EFECTIVO, TRANSFERENCIA
  - 1 Usuario admin@foodstore.com con rol ADMIN
- Campos de auditoría: `creado_en`, `actualizado_en` en todas las tablas principales

---

### ✅ change: `backend-patterns-base-repository-uow`
**Funcionalidad**: Implementación de patrones de infraestructura: BaseRepository genérico, Unit of Work, dependencias FastAPI.

**Historias**: US-000d

**Dependencias**: `backend-postgres-alembic-seed`

**Descripción**:
- Implementar `BaseRepository[T]` genérico con métodos: `get_by_id()`, `list_all()`, `count()`, `create()`, `update()`, `soft_delete()`, `hard_delete()`
- Excluir soft-delete por defecto en listados
- Implementar `UnitOfWork` como context manager async:
  - Abre sesión SQLAlchemy en `__aenter__`
  - Expone repositorios como atributos
  - Hace `commit()` al salir sin excepciones
  - Ejecuta `rollback()` automáticamente si hay error
- Implementar dependencia `get_current_user()` (extrae JWT, valida, retorna Usuario)
- Implementar factory `require_role(roles: list[str])` (verifica roles, lanza 403 si no tiene)
- Middleware global de errores RFC 7807

---

### ✅ change: `frontend-react-vite-setup`
**Funcionalidad**: Setup del frontend React, TypeScript, Vite, dependencias core.

**Historias**: US-000c

**Dependencias**: `infrastructure-repo-setup`

**Descripción**:
- Crear proyecto React + TypeScript + Vite
- Instalar dependencias: react-router-dom, @tanstack/react-query, @tanstack/react-form, zustand, axios, recharts, tailwindcss, @mercadopago/sdk-js
- Configurar TypeScript en modo estricto (`strict: true`)
- Configurar Tailwind CSS + PostCSS
- Configurar Axios con base URL desde `VITE_API_BASE_URL`
- Crear routing base con React Router (público y privado)
- Configurar QueryClient con TanStack Query en App root
- Crear `.env.example` con variables necesarias

---

### ✅ change: `frontend-zustand-stores-setup`
**Funcionalidad**: Implementación de 4 stores Zustand con persistencia selectiva.

**Historias**: US-000e

**Dependencias**: `frontend-react-vite-setup`

**Descripción**:
- Implementar `authStore`: tokens, usuario, isAuthenticated. Acciones: login(), logout(), updateTokens(). Persistencia: solo accessToken. Métodos helper: hasRole(role)
- Implementar `cartStore`: items (CartItem[]), acciones: addItem(), removeItem(), updateQuantity(), clearCart(). Selectores: totalItems(), totalPrice(). Persistencia: items completos
- Implementar `paymentStore`: checkoutStep, preferenceId, paymentStatus. Acciones: startCheckout(), setPreference(), updatePaymentStatus(), resetPayment(). SIN persistencia
- Implementar `uiStore`: theme, sidebarOpen, toasts. Persistencia selectiva: solo theme
- Todos usan suscripción por slice

---

### ✅ change: `backend-axios-jwt-interceptor`
**Funcionalidad**: Configuración de Axios con interceptor JWT para frontend.

**Historias**: US-066

**Dependencias**: `frontend-zustand-stores-setup`

**Descripción**:
- Crear instancia centralizada de Axios en `shared/api/axios.ts`
- Interceptor de request: adjunta `Authorization: Bearer <token>` del authStore
- Interceptor de response: detecta 401 (token expirado)
  - Intenta refresh con refreshToken
  - Actualiza authStore con nuevos tokens
  - Reintenta request original
  - Cola de requests para evitar múltiples refresh simultáneos
- Fallback: si refresh falla, redirige al login

---

### ✅ change: `backend-error-handling-rfc7807`
**Funcionalidad**: Manejo de errores estandarizado con RFC 7807.

**Historias**: US-068

**Dependencias**: `backend-fastapi-core-setup`

**Descripción**:
- Crear middleware global que captura excepciones y las formatea como RFC 7807
- Estructura: `{ type, title, status, detail, instance }`
- Errores de validación incluyen detalles por campo
- No exponer stack traces en producción
- Loguear errores 500 con stack trace en servidor

---

### ✅ change: `backend-input-validation-sanitization`
**Funcionalidad**: Validación y sanitización de inputs.

**Historias**: US-074

**Dependencias**: `backend-fastapi-core-setup`

**Descripción**:
- Schemas Pydantic v2 para todos los requests
- Validaciones: emails, longitudes, rangos numéricos
- Queries parametrizadas (SQLModel previene SQL injection)
- Sanitización contra XSS en campos de texto

---

## EPIC 01 — Autenticación y Autorización

### ✅ change: `auth-registration`
**Funcionalidad**: Registro de nuevos clientes.

**Historias**: US-001

**Dependencias**: `backend-patterns-base-repository-uow`

**Descripción**:
- Endpoint `POST /api/v1/auth/register` con schema RegisterRequest
- Validar email único, contraseña mínimo 8 caracteres, nombre mínimo 2 caracteres
- Hashear contraseña con bcrypt (cost factor >= 10)
- Asignar rol CLIENT automáticamente (NO viene del request)
- Retornar access token (30 min) + refresh token (7 días) + datos usuario
- Campos de auditoría: creado_en, actualizado_en

---

### ✅ change: `auth-login`
**Funcionalidad**: Login de usuario con JWT y rate limiting.

**Historias**: US-002, US-073

**Dependencias**: `auth-registration`

**Descripción**:
- Endpoint `POST /api/v1/auth/login` con schema LoginRequest
- Rate limiting: máximo 5 intentos fallidos por IP en 15 minutos (slowapi)
- Verificar credenciales contra BD (bcrypt)
- NO diferenciar "email no existe" vs "contraseña incorrecta"
- Generar JWT access token (30 min, payload: userId, email, roles, HS256)
- Generar refresh token UUID, almacenar en tabla RefreshToken con expires_at (7 días)
- Retornar TokenResponse: access_token, refresh_token, token_type="Bearer", usuario

---

### ✅ change: `auth-token-refresh`
**Funcionalidad**: Renovación automática de tokens JWT.

**Historias**: US-003

**Dependencias**: `auth-login`

**Descripción**:
- Endpoint `POST /api/v1/auth/refresh` con refresh token
- Validar que el token existe en BD, no esté expirado, no esté revocado
- Implementar rotación: marcar refresh token anterior como revocado (revoked_at = now)
- Emitir nuevo par access + refresh token
- Detectar replay attack: si se usa un token ya revocado, revocar TODOS los tokens del usuario
- Retornar TokenResponse con nuevos tokens

---

### ✅ change: `auth-logout`
**Funcionalidad**: Cierre de sesión.

**Historias**: US-004

**Dependencias**: `auth-login`

**Descripción**:
- Endpoint `POST /api/v1/auth/logout` con refresh token
- Marcar refresh token como revocado (revoked_at = now)
- Frontend limpia authStore + localStorage
- Retornar 204 No Content

---

### ✅ change: `rbac-roles-management`
**Funcionalidad**: Gestión de roles RBAC (Role-Based Access Control).

**Historias**: US-005

**Dependencias**: `auth-registration`

**Descripción**:
- Implementar 4 roles fijos: ADMIN, STOCK, PEDIDOS, CLIENT
- Almacenar en tabla Rol con PK semántica
- Relación N:M Usuario-Rol con restricción UNIQUE compuesta
- Endpoint `PUT /api/admin/users/:id/role` para asignar roles (solo ADMIN)
- Validar: ADMIN no puede quitarse el rol ADMIN a sí mismo si es el último admin
- Asignar CLIENT automáticamente en registro

---

### ✅ change: `route-protection-rbac`
**Funcionalidad**: Middleware de protección de rutas por rol.

**Historias**: US-006

**Dependencias**: `rbac-roles-management`

**Descripción**:
- Dependencia `require_role(roles: list[str])` que verifica roles del JWT
- Endpoints públicos: /api/v1/auth/*, /api/v1/productos (GET), /api/v1/categorias (GET)
- Endpoints protegidos por rol: ADMIN, STOCK, PEDIDOS, CLIENT
- Retornar 401 sin token válido, 403 si rol insuficiente
- Incluir en todos los routers

---

### ✅ change: `frontend-navigation-by-role`
**Funcionalidad**: Menú de navegación adaptado al rol del usuario.

**Historias**: US-075

**Dependencias**: `rbac-roles-management`

**Descripción**:
- Componente Navigation/Sidebar con menú dinámico
- CLIENT ve: Catálogo, Mi Carrito, Mis Pedidos, Mi Perfil, Mis Direcciones
- STOCK ve: Productos, Categorías, Ingredientes, Stock
- PEDIDOS ve: Panel de Pedidos
- ADMIN ve: todas las opciones + Usuarios + Métricas + Configuración
- No autenticado: Catálogo, Login, Registrarse
- Guard de rutas en frontend basado en rol del JWT

---

### ✅ change: `frontend-route-guards-auth`
**Funcionalidad**: Guards de navegación por autenticación y rol en frontend.

**Historias**: US-076

**Dependencias**: `frontend-navigation-by-role`

**Descripción**:
- HOC `withAuth(Component, requiredRoles)` que protege rutas
- Redirigir a login si no autenticado
- Mostrar pantalla 403 si rol insuficiente
- Rutas públicas (catálogo, login, registro) accesibles sin auth
- Usar authStore como source of truth

---

### ✅ change: `frontend-error-handling-global`
**Funcionalidad**: Manejo centralizado de errores HTTP en frontend.

**Historias**: US-067

**Dependencias**: `backend-error-handling-rfc7807`

**Descripción**:
- Error boundary global en React
- Interceptor Axios que mapea HTTP status codes a mensajes
  - 400: "Verifica tus datos"
  - 403: "No tienes permisos"
  - 404: "Recurso no encontrado"
  - 429: "Demasiadas solicitudes, espera un momento"
  - 500: "Error interno, intenta más tarde"
- Sistema de toasts para notificaciones de error

---

## EPIC 02 — Navegación y Layout Base

### ✅ change: `frontend-layout-components-shared`
**Funcionalidad**: Componentes base compartidos (Navbar, Sidebar, Footer, Buttons, Inputs, Modals, etc.).

**Historias**: (soporte para todas las historias de UI)

**Dependencias**: `frontend-route-guards-auth`

**Descripción**:
- Componente Layout con Navbar, Sidebar, main content, Footer
- Componentes atómicos: Button, Input, Card, Modal, Toast, Skeleton, Badge
- Sistema de iconos (lucide-react)
- Variables Tailwind (colores, espacios, tipografía)
- Responsive design mobile-first

---

## EPIC 03 — Gestión de Categorías

### ✅ change: `categories-crud-hierarchical`
**Funcionalidad**: CRUD de categorías con jerarquía recursiva.

**Historias**: US-007, US-008, US-009, US-010

**Dependencias**: `route-protection-rbac`

**Descripción**:
- Modelo Categoria con `padre_id` (FK autoreferencial)
- Endpoints:
  - `POST /api/v1/categorias` (STOCK, ADMIN)
  - `GET /api/v1/categorias` (público, retorna árbol anidado)
  - `PUT /api/v1/categorias/:id` (STOCK, ADMIN)
  - `DELETE /api/v1/categorias/:id` (soft delete, STOCK, ADMIN)
- Validación: no crear ciclos (CTE recursivo)
- No eliminar categorías con productos activos asociados
- Soft delete con `eliminado_en`

---

## EPIC 04 — Gestión de Ingredientes y Alergenos

### ✅ change: `ingredients-crud-allergens`
**Funcionalidad**: CRUD de ingredientes con flag de alérgeno.

**Historias**: US-011, US-012, US-013, US-014

**Dependencias**: `route-protection-rbac`

**Descripción**:
- Modelo Ingrediente con campos: id, nombre (UNIQUE), es_alergeno (booleano)
- Endpoints:
  - `POST /api/v1/ingredientes` (STOCK, ADMIN)
  - `GET /api/v1/ingredientes?esAlergeno=true` (STOCK, ADMIN, paginado)
  - `PUT /api/v1/ingredientes/:id` (STOCK, ADMIN)
  - `DELETE /api/v1/ingredientes/:id` (soft delete, STOCK, ADMIN)
- Validar unicidad de nombre

---

## EPIC 05 — Gestión de Productos y Catálogo

### ✅ change: `products-crud-core`
**Funcionalidad**: CRUD básico de productos.

**Historias**: US-015, US-020, US-021, US-022

**Dependencias**: `route-protection-rbac`

**Descripción**:
- Modelo Producto con: id, nombre, descripcion, precio_base (NUMERIC(10,2)), stock_cantidad (INTEGER), disponible (BOOLEAN), imagen_url, creado_en, actualizado_en, eliminado_en
- Endpoints:
  - `POST /api/v1/productos` (STOCK, ADMIN)
  - `GET /api/v1/productos` (público, paginado, filtros)
  - `GET /api/v1/productos/:id` (público)
  - `PUT /api/v1/productos/:id` (STOCK, ADMIN)
  - `PATCH /api/v1/productos/:id/stock` (STOCK, ADMIN, UoW)
  - `DELETE /api/v1/productos/:id` (soft delete, STOCK, ADMIN)
- Validaciones: precio > 0, stock >= 0, disponible es booleano
- Soft delete con `eliminado_en`

---

### ✅ change: `products-categories-association`
**Funcionalidad**: Asociación N:M de productos a categorías.

**Historias**: US-016

**Dependencias**: `products-crud-core`, `categories-crud-hierarchical`

**Descripción**:
- Tabla pivote ProductoCategoria (producto_id, categoria_id) con PK compuesta
- Endpoints:
  - `PUT /api/v1/productos/:id/categorias` (STOCK, ADMIN) — body: array de categoryIds
  - `DELETE /api/v1/productos/:id/categorias/:cat_id` (STOCK, ADMIN)
- Un producto puede pertenecer a múltiples categorías

---

### ✅ change: `products-ingredients-association`
**Funcionalidad**: Asociación N:M de productos a ingredientes.

**Historias**: US-017, US-023

**Dependencias**: `products-crud-core`, `ingredients-crud-allergens`

**Descripción**:
- Tabla pivote ProductoIngrediente (producto_id, ingrediente_id) con es_removible (booleano)
- Endpoints:
  - `PUT /api/v1/productos/:id/ingredientes` (STOCK, ADMIN) — body: array de ingredientIds
  - `DELETE /api/v1/productos/:id/ingredientes/:ing_id` (STOCK, ADMIN)
- Los ingredientes marcados como es_alergeno se destacan en el frontend
- Filtro en catálogo: `GET /api/v1/productos?excluirAlergenos=1,3,7`

---

### ✅ change: `products-catalog-public`
**Funcionalidad**: Catálogo público de productos con filtros y búsqueda.

**Historias**: US-018, US-019

**Dependencias**: `products-categories-association`, `products-ingredients-association`

**Descripción**:
- Endpoint `GET /api/v1/productos` (público, sin auth)
  - Parámetros: `?categoria=5&busqueda=pizza&page=1&limit=20&excluirAlergenos=1,3`
  - Filtra: disponible=true, eliminado_en IS NULL
  - Soporta paginación con total
  - Soporta búsqueda por nombre (ILIKE)
  - Soporta filtro por categoría
  - Soporta exclusión de alergenos
- Endpoint `GET /api/v1/productos/:id` (público)
  - Retorna: nombre, descripcion, precio, imagen, stock > 0 (sin cantidad exacta), categorias, ingredientes con es_alergeno

---

### ✅ change: `frontend-products-catalog-ui`
**Funcionalidad**: Interfaz de usuario del catálogo de productos.

**Historias**: US-018, US-019

**Dependencias**: `products-catalog-public`, `frontend-layout-components-shared`

**Descripción**:
- Página Catalog con grid de productos
- Componentes: ProductCard (imagen, nombre, precio, disponible), ProductDetail modal
- Filtros: por categoría, búsqueda con debounce, exclusión de alergenos
- Paginación
- Skeleton loaders durante carga
- Botón "Agregar al carrito" en cada producto

---

## EPIC 06 — Gestión de Direcciones de Entrega

### ✅ change: `addresses-crud-by-user`
**Funcionalidad**: CRUD de direcciones de entrega por usuario.

**Historias**: US-024, US-025, US-026, US-027, US-028

**Dependencias**: `route-protection-rbac`

**Descripción**:
- Modelo DireccionEntrega: id, usuario_id, alias, linea1, piso, departamento, ciudad, codigo_postal, referencia, es_principal (BOOLEAN), creado_en, actualizado_en, eliminado_en
- Endpoints (protegidos por CLIENT):
  - `POST /api/v1/direcciones` (crear)
  - `GET /api/v1/direcciones` (listar propias)
  - `GET /api/v1/direcciones/:id` (detalle propia)
  - `PUT /api/v1/direcciones/:id` (actualizar propia)
  - `PATCH /api/v1/direcciones/:id/principal` (marcar como principal)
  - `DELETE /api/v1/direcciones/:id` (soft delete)
- Validaciones: solo un usuario puede ver/editar sus propias direcciones (RN-RB05)
- La primera dirección se marca como principal automáticamente
- Solo una dirección principal por usuario en cada momento

---

### ✅ change: `frontend-addresses-ui`
**Funcionalidad**: Interfaz de gestión de direcciones.

**Historias**: US-024, US-025, US-026, US-027, US-028

**Dependencias**: `addresses-crud-by-user`, `frontend-layout-components-shared`

**Descripción**:
- Página MyAddresses con listado de direcciones
- Componente AddressCard con opciones: editar, eliminar, marcar como principal
- Form AddressForm para crear/editar
- Integración con cartStore: mostrar dirección principal en checkout

---

## EPIC 07 — Carrito de Compras (Client-Side)

### ✅ change: `frontend-shopping-cart-zustand`
**Funcionalidad**: Carrito de compras con persistencia en localStorage.

**Historias**: US-029, US-030, US-031, US-032, US-033, US-034

**Dependencias**: `frontend-zustand-stores-setup`

**Descripción**:
- cartStore ya existe (US-000e), aquí se completa la lógica:
  - addItem(producto, cantidad, personalizacion)
  - removeItem(productoId)
  - updateQuantity(productoId, cantidad)
  - clearCart()
  - Selectores: totalItems(), totalPrice(), getItem(productoId)
  - Persistencia: localStorage con clave "food-store-cart"
- Personalización: almacenar array de IDs de ingredientes a excluir
- Si producto ya está en carrito, incrementar cantidad (no duplicar)
- Carrito sobrevive: cierre navegador, refresh de página, logout/login

---

### ✅ change: `frontend-shopping-cart-ui`
**Funcionalidad**: Interfaz del carrito de compras.

**Historias**: US-029, US-030, US-031, US-032, US-033, US-034

**Dependencias**: `frontend-shopping-cart-zustand`, `frontend-layout-components-shared`

**Descripción**:
- Componente CartDrawer (sidebar):
  - Listar items con nombre, precio, cantidad, subtotal
  - Botones: +/-, eliminar, vaciar carrito
  - Mostrar total + costo envío + total final
  - Botón "Ir a Checkout"
- Componente CartIcon en Navbar con contador de items
- Personalización UI: mostrar ingredientes excluidos
- Estado vacío: "Tu carrito está vacío"

---

## EPIC 08 — Perfil de Cliente

### ✅ change: `frontend-user-profile-ui`
**Funcionalidad**: Visualización y edición del perfil del cliente.

**Historias**: US-061, US-062, US-063, US-064, US-065

**Dependencias**: `route-protection-rbac`, `frontend-layout-components-shared`

**Descripción**:
- Página MyProfile con datos: nombre, email, teléfono, fecha de registro
- Form para editar nombre y teléfono
- Endpoint backend `GET /api/v1/perfil` y `PUT /api/v1/perfil`
- Cambio de contraseña: endpoint `POST /api/v1/perfil/cambiar-password`
- Validar contraseña anterior antes de permitir cambio
- Mostrar última vez logueo
- Botón para descargar datos personales (GDPR compliance)

---

### ✅ change: `backend-user-profile-endpoints`
**Funcionalidad**: Endpoints de gestión del perfil del usuario.

**Historias**: US-061, US-062, US-063, US-064, US-065

**Dependencias**: `route-protection-rbac`

**Descripción**:
- `GET /api/v1/perfil` (CLIENT) — retorna UserResponse completo
- `PUT /api/v1/perfil` (CLIENT) — actualiza nombre, teléfono
- `POST /api/v1/perfil/cambiar-password` (CLIENT) — cambiar contraseña
  - Validar contraseña actual
  - Nueva contraseña debe cumplir requisitos (8+ caracteres)
  - Hashear con bcrypt
- Campos no modificables: email, rol, fechas de creación

---

## EPIC 09 — Pedidos (Creación y Estados)

### ✅ change: `orders-fsm-backend`
**Funcionalidad**: Máquina de estados de pedidos (FSM) en backend.

**Historias**: US-035, US-036, US-037, US-038, US-039, US-040, US-041, US-042, US-043, US-044

**Dependencias**: `backend-patterns-base-repository-uow`, `addresses-crud-by-user`, `products-crud-core`

**Descripción**:
- Modelos: Pedido, DetallePedido, HistorialEstadoPedido, EstadoPedido (catálogo)
- Estados: PENDIENTE → CONFIRMADO → EN_PREPARACIÓN → EN_CAMINO → ENTREGADO (con CANCELADO desde cualquier estado pre-terminal)
- Tabla HistorialEstadoPedido append-only (solo INSERT, nunca UPDATE/DELETE)
- Snapshot pattern: guardar precio, nombre, dirección al crear pedido
- Servicio de creación de pedido (UoW atómico):
  - Validar usuario, dirección, forma de pago, productos (stock suficiente)
  - Crear snapshots de precios y dirección
  - Crear Pedido con estado PENDIENTE
  - Crear DetallePedido para cada item
  - Crear HistorialEstadoPedido inicial (estado_desde=NULL)
  - Rollback si falla en cualquier paso
- Servicio de avance de estado:
  - Validar transición contra máquina de estados
  - Si PENDIENTE → CONFIRMADO: decrementar stock atómicamente
  - Crear registro en HistorialEstadoPedido
  - Validar permisos por rol
- Servicio de cancelación:
  - Si CONFIRMADO: restaurar stock
  - Si EN_PREPARACIÓN: solo ADMIN
  - Crear HistorialEstadoPedido con observación

---

### ✅ change: `orders-api-endpoints`
**Funcionalidad**: Endpoints REST para gestión de pedidos.

**Historias**: US-035, US-036, US-039, US-040, US-041, US-042, US-043, US-044

**Dependencias**: `orders-fsm-backend`

**Descripción**:
- `POST /api/v1/pedidos` (CLIENT) — crear pedido
  - Body: CrearPedidoRequest (items, forma_pago_id, direccion_id)
  - Respuesta: PedidoRead (201)
  - UoW atómico
- `GET /api/v1/pedidos` (CLIENT/ADMIN/PEDIDOS) — listar
  - CLIENT: solo propios
  - ADMIN/PEDIDOS: todos
  - Filtros: estado, fecha, paginación
- `GET /api/v1/pedidos/:id` (propietario/ADMIN) — detalle completo
  - Retorna: PedidoDetail con items, historial, pagos, snapshots
- `PATCH /api/v1/pedidos/:id/avanzar` (ADMIN/PEDIDOS) — avanzar estado
  - Body: AvanzarEstadoRequest (observación opcional)
- `GET /api/v1/pedidos/:id/historial` (propietario/ADMIN) — audit trail
  - Retorna array de transiciones ordenado por fecha
- `DELETE /api/v1/pedidos/:id` (CLIENT propietario) — cancelar
  - Solo si PENDIENTE o CONFIRMADO
  - Restaura stock si CONFIRMADO

---

### ✅ change: `frontend-orders-listing-ui`
**Funcionalidad**: Interfaz de listado de pedidos del cliente.

**Historias**: US-049, US-050, US-051

**Dependencias**: `orders-api-endpoints`, `frontend-layout-components-shared`

**Descripción**:
- Página MyOrders para CLIENT: lista sus propios pedidos
- Página OrdersPanel para ADMIN/PEDIDOS: lista todos los pedidos
- Componente OrderCard: id, fecha, estado (badge de color), total, acción: ver detalles
- Paginación
- Filtros: por estado, por fecha
- Skeleton loaders

---

### ✅ change: `frontend-orders-detail-ui`
**Funcionalidad**: Interfaz de detalle de pedido con trazabilidad.

**Historias**: US-052, US-053

**Dependencias**: `orders-api-endpoints`, `frontend-layout-components-shared`

**Descripción**:
- Página OrderDetail
- Mostrar: id, estado actual, fecha de creación, total, detalles de items (nombre, cantidad, precio snapshot, personalizacion)
- Mostrar dirección de entrega (snapshot)
- Mostrar forma de pago
- Timeline de estados (HistorialEstadoPedido):
  - Para cada transición: fecha, estado anterior → nuevo, usuario responsable (o "Sistema"), observación
  - Botones de acción según estado y rol:
    - CONFIRMADO (ADMIN/PEDIDOS): avanzar a EN_PREPARACIÓN
    - EN_PREPARACIÓN (ADMIN/PEDIDOS): avanzar a EN_CAMINO
    - EN_CAMINO (ADMIN/PEDIDOS): avanzar a ENTREGADO
    - PENDIENTE/CONFIRMADO (CLIENT): cancelar con confirmación

---

### ✅ change: `frontend-orders-management-admin`
**Funcionalidad**: Panel de administración de pedidos.

**Historias**: US-071, US-072

**Dependencias**: `frontend-orders-listing-ui`, `frontend-orders-detail-ui`

**Descripción**:
- Página OrdersManagement (ADMIN/PEDIDOS only)
- Tabla con columnas: id, cliente, fecha, estado, total, acciones
- Filtros: por estado, por fecha, por cliente
- Acciones: ver detalle, avanzar estado, cancelar (solo si ADMIN en EN_PREPARACIÓN)
- Bulk actions: cambiar estado múltiples órdenes
- Búsqueda por ID de pedido

---

## EPIC 10 — Pagos (MercadoPago)

### ✅ change: `payments-mercadopago-integration-backend`
**Funcionalidad**: Integración backend con MercadoPago Checkout API.

**Historias**: US-045, US-046, US-047, US-048

**Dependencias**: `orders-fsm-backend`

**Descripción**:
- Modelo Pago: id, pedido_id, mp_payment_id (UNIQUE, NULL), mp_status, external_reference (UUID del pedido), idempotency_key (UUID), creado_en, actualizado_en
- Servicio de creación de pago:
  - Endpoint `POST /api/v1/pagos/crear` (CLIENT)
  - Body: { pedido_id, card_token (tokenizado por SDK MP) }
  - Generar idempotency_key UUID
  - Llamar API MercadoPago con card_token y external_reference
  - Registrar Pago con mp_payment_id y mp_status
  - Retornar estado
- Webhook IPN:
  - Endpoint `POST /api/v1/pagos/webhook` (público, validar firma MP)
  - Procesar topic=payment
  - Consultar MercadoPago API con mp_payment_id para obtener estado actual
  - Actualizar tabla Pago
  - Si approved: ejecutar transición PENDIENTE → CONFIRMADO (UoW) + decremento de stock
  - Responder HTTP 200 inmediatamente para evitar reintentos
- Consulta de pagos:
  - Endpoint `GET /api/v1/pagos/:pedido_id` (propietario/ADMIN)
  - Retorna array de intentos de pago

---

### ✅ change: `frontend-payment-checkout-ui`
**Funcionalidad**: Interfaz de checkout con pago MercadoPago.

**Historias**: US-045, US-046, US-047, US-048

**Dependencias**: `payments-mercadopago-integration-backend`, `addresses-crud-by-user`, `frontend-shopping-cart-zustand`

**Descripción**:
- Página Checkout con pasos:
  1. Resumen del carrito (items, precios)
  2. Seleccionar dirección de entrega
  3. Seleccionar forma de pago (MERCADOPAGO, EFECTIVO, TRANSFERENCIA)
  4. Confirmar pedido → crear en backend
  5. Si MercadoPago: renderizar CardPayment del SDK
- Componente CardPayment (SDK MercadoPago):
  - Campos: número tarjeta, vencimiento, CVV, titular
  - SDK tokeniza a card_token (nunca pasa por servidor)
  - Botón "Pagar" llama POST /api/v1/pagos/crear
- Estados de pago:
  - "Procesando..." durante request
  - "Pago aprobado" → redirigir a OrderDetail
  - "Pago rechazado" → mostrar error con opción de reintentar
  - "Pago pendiente" → redirigir a OrderDetail (estado PENDIENTE)
- Integración paymentStore: setPaymentStatus(), updatePaymentStatus()

---

### ✅ change: `frontend-payment-status-polling`
**Funcionalidad**: Polling de estado de pago en frontend.

**Historias**: US-046, US-047

**Dependencias**: `frontend-payment-checkout-ui`

**Descripción**:
- En OrderDetail, si estado PENDIENTE: polling cada 30 segundos a `GET /api/v1/pagos/:pedido_id`
- Verificar mp_status:
  - Si approved → actualizar estado a CONFIRMADO
  - Si rejected → mostrar error
  - Si pending/in_process → seguir esperando
- Detectar cambios de estado mediante cambio de timestamp en tabla Pago
- Detener polling cuando estado no sea PENDIENTE

---

## EPIC 11 — Panel de Administración

### ✅ change: `admin-dashboard-metrics`
**Funcionalidad**: Dashboard de métricas de negocio.

**Historias**: US-57, US-58, US-59, US-60

**Dependencias**: `orders-fsm-backend`, `products-crud-core`

**Descripción**:
- Endpoint `GET /api/v1/admin/metricas` (ADMIN only)
  - Total de pedidos (todos, completados, cancelados, pendientes)
  - Ingresos totales (suma de totales de pedidos ENTREGADO/CONFIRMADO)
  - Productos más vendidos (top 10)
  - Clientes más activos (top 10)
  - Pedidos por estado (conteos)
  - Ingresos por mes (últimos 12 meses)
  - Stock bajo (productos con stock < 5)
- Caching opcional: invalidar cuando hay cambios en pedidos/stock

---

### ✅ change: `frontend-admin-dashboard-ui`
**Funcionalidad**: Interfaz visual del dashboard de administración.

**Historias**: US-57, US-58, US-59, US-60

**Dependencias**: `admin-dashboard-metrics`, `frontend-layout-components-shared`

**Descripción**:
- Página AdminDashboard (ADMIN only)
- KPI cards: total pedidos, ingresos, productos, clientes
- Gráficos (recharts):
  - Línea: ingresos por mes
  - Barra: pedidos por estado
  - Pastel: top 10 productos más vendidos
  - Tabla: alertas de stock bajo
- Responsive: adaptar gráficos a mobile
- Refresh automático cada 5 minutos (o manual con botón)

---

### ✅ change: `admin-categories-management-ui`
**Funcionalidad**: CRUD de categorías desde panel admin.

**Historias**: (complemento a US-007, US-008, US-009, US-010)

**Dependencias**: `categories-crud-hierarchical`, `frontend-layout-components-shared`

**Descripción**:
- Página AdminCategories (ADMIN, STOCK only)
- Tabla con columnas: id, nombre, padre, acciones
- Formulario crear/editar categoría
- Relación padre-hijo mediante select de categorías
- Validación: no crear ciclos (backend valida)
- Soft delete con confirmación
- Dragable reordenar jerarquía (opcional)

---

### ✅ change: `admin-products-management-ui`
**Funcionalidad**: CRUD de productos desde panel admin.

**Historias**: (complemento a US-015, US-016, US-017, US-020, US-021, US-022)

**Dependencias**: `products-crud-core`, `products-categories-association`, `products-ingredients-association`, `frontend-layout-components-shared`

**Descripción**:
- Página AdminProducts (ADMIN, STOCK only)
- Tabla con columnas: id, nombre, precio, stock_cantidad, disponible, acciones
- Formulario crear/editar producto con:
  - Campos básicos: nombre, descripción, precio, stock, imagen (upload)
  - Asociación de categorías (multi-select)
  - Asociación de ingredientes (multi-select con toggle es_removible)
  - Toggle disponible
- Filtros: por categoría, por nombre
- Bulk actions: cambiar disponibilidad, cambiar precio
- Soft delete con confirmación
- Preview de cambios antes de guardar

---

### ✅ change: `admin-stock-management-ui`
**Funcionalidad**: Gestión de stock desde panel admin.

**Historias**: US-021 (complemento)

**Dependencias**: `admin-products-management-ui`

**Descripción**:
- Página AdminStock (ADMIN, STOCK only)
- Tabla con columnas: id, nombre, stock_cantidad, disponible, last_updated, acciones
- Campos editables inline: stock_cantidad
- Acciones: incrementar/decrementar, marcar disponible/no disponible
- Filtros: por nivel de stock (bajo < 5, crítico < 2, etc.)
- Historial de cambios de stock (opcional, auditoría)
- Alertas visuales para stock bajo/crítico

---

### ✅ change: `admin-users-management-ui`
**Funcionalidad**: Gestión de usuarios desde panel admin.

**Historias**: US-005, US-054, US-055

**Dependencias**: `rbac-roles-management`, `frontend-layout-components-shared`

**Descripción**:
- Página AdminUsers (ADMIN only)
- Tabla con columnas: id, nombre, email, roles, creado_en, acciones
- Formulario crear/editar usuario:
  - Email, nombre, teléfono
  - Asignación de roles (checkboxes, múltiples)
- Acciones: editar, soft delete (desactivar), cambiar contraseña (generar temporal)
- Filtros: por rol
- Búsqueda por nombre/email
- Validación ADMIN: no puede quitarse ADMIN a sí mismo si es último admin

---

### ✅ change: `admin-ingredients-management-ui`
**Funcionalidad**: Gestión de ingredientes desde panel admin.

**Historias**: (complemento a US-011, US-012, US-013, US-014)

**Dependencias**: `ingredients-crud-allergens`, `frontend-layout-components-shared`

**Descripción**:
- Página AdminIngredients (ADMIN, STOCK only)
- Tabla con columnas: id, nombre, es_alergeno (toggle), productos (count), acciones
- Formulario crear/editar ingrediente
- Toggle es_alergeno
- Soft delete con confirmación
- Mostrar en qué productos está usado (informativo)

---

## EPIC 12 — Completude y Validaciones

### ✅ change: `backend-comprehensive-testing`
**Funcionalidad**: Suite de tests unitarios e integración.

**Historias**: (bonus +10 pts según rúbrica)

**Dependencias**: (todos los changes anteriores)

**Descripción**:
- Tests pytest con cobertura > 60%:
  - test_auth.py: login, registro, refresh, logout, rate limiting
  - test_orders.py: creación, FSM, cancelación, stock
  - test_payments.py: webhook IPN, idempotency_key
  - test_categories.py: CRUD, jerarquía, ciclos
  - test_products.py: CRUD, stock, soft delete
- Fixtures para usuario, pedido, producto
- Mocking de MercadoPago SDK
- Tests de integración con BD real (test database)

---

### ✅ change: `documentation-openapi-complete`
**Funcionalidad**: Documentación automática OpenAPI completa.

**Historias**: (entrega CE-08)

**Dependencias**: (todos los routers implementados)

**Descripción**:
- Swagger UI en `/docs` con todos los endpoints documentados
- ReDoc en `/redoc`
- Describir request/response bodies con ejemplos
- Describir códigos de error esperados
- Documentar autenticación (bearer token)
- Documentar rate limiting

---

### ✅ change: `repository-setup-final-checklist`
**Funcionalidad**: Verificación final de entrega.

**Historias**: (entrega CE-01 a CE-14)

**Dependencias**: (todos los changes anteriores)

**Descripción**:
- README.md completo con instrucciones de setup
- `.env.example` con todas las variables documentadas
- `.gitignore` correcto (excluyendo `.env`, `__pycache__`, `node_modules`, etc.)
- Repositorio público en GitHub
- Commits con conventional commits
- Screenshots de al menos 10 pantallas
- Video de demostración (5-10 min)
- Verificar que el proyecto funciona en máquina limpia

---

## Orden de Implementación Recomendado

```
BLOQUE 1 (Infraestructura)
├─ infrastructure-repo-setup
├─ backend-fastapi-core-setup
├─ backend-dev-infrastructure
├─ backend-postgres-alembic-seed
├─ backend-patterns-base-repository-uow
├─ frontend-react-vite-setup
├─ frontend-zustand-stores-setup
├─ backend-axios-jwt-interceptor
├─ backend-error-handling-rfc7807
└─ backend-input-validation-sanitization
```

---

## Notas Importantes

1. **Un change = un commit (o varios commits atómicos)**: Nunca mezcles dos changes en un mismo commit.
2. **Order importa**: Si el change B necesita código del change A, A debe estar archivado antes de proponer B.
3. **Historial de cambios**: Una vez archivado un change, sus specs quedan disponibles para los cambios futuros en `openspec/specs/`.
4. **Patrones base**: Los changes de BLOQUE 1 son fundamentales — el resto depende de ellos. No saltear.
5. **Testing**: El testing (BLOQUE 10) NO es opcional, es obligatorio según la rúbrica.
6. **Dependencias externas**: MercadoPago requiere credenciales en `.env` (variables MP_ACCESS_TOKEN, MP_PUBLIC_KEY).

---

## Historial de Cambios

| Versión | Fecha      | Cambios                                         |
|---------|------------|-----------------------------------------------|
| 2.0     | 24/04/2026 | Agregado CHANGE 2.5 (backend-dev-infrastructure) — Docker, psycopg[binary], seed idempotente |
| 1.0     | 21/04/2026 | Documento inicial con mapeo completo de changes |

---

## Referencia Rápida

- **Backend entrypoint**: `app/main.py`
- **Frontend entrypoint**: `src/App.tsx`
- **Base de datos**: PostgreSQL (CONNECTION STRING en `.env`)
- **ORM**: SQLModel
- **API Framework**: FastAPI
- **UI Framework**: React + TypeScript + Tailwind
- **Documentación API**: `/docs` (Swagger UI)
