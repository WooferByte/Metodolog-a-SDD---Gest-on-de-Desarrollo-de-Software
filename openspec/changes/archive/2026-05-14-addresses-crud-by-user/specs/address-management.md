# Spec — address-management

## Capability

CRUD completo de direcciones de entrega por usuario autenticado.

## Endpoints

### POST /api/v1/direcciones

Crear nueva dirección de entrega para el usuario autenticado.

**Auth**: Bearer JWT (usuario autenticado, cualquier rol)
**Request body**: `DireccionCreate`
**Response**: `201 Created` con `DireccionResponse`

**Reglas**:
- RN-DI01: si es la primera dirección activa del usuario → `es_predeterminada=True` automático, independientemente del valor enviado en el body
- Si el body incluye `es_predeterminada=True` y no es la primera → aplicar RN-DI02: desmarcar todas las demás antes de crear

---

### GET /api/v1/direcciones

Listar todas las direcciones activas del usuario autenticado.

**Auth**: Bearer JWT
**Response**: `200 OK` con `list[DireccionResponse]`

**Reglas**:
- Solo retorna direcciones con `eliminado_en IS NULL`
- Solo retorna direcciones del `usuario_id` del JWT
- Ordenadas por `creado_en DESC`

---

### GET /api/v1/direcciones/{id}

Obtener una dirección específica del usuario autenticado.

**Auth**: Bearer JWT
**Response**: `200 OK` con `DireccionResponse`

**Reglas**:
- RN-DI03: si la dirección existe pero pertenece a otro usuario → `403 Forbidden`
- Si no existe (o fue soft-deleted) → `404 Not Found`

---

### PUT /api/v1/direcciones/{id}

Actualizar parcialmente una dirección del usuario autenticado.

**Auth**: Bearer JWT
**Request body**: `DireccionUpdate` (todos los campos opcionales)
**Response**: `200 OK` con `DireccionResponse`

**Reglas**:
- RN-DI03: ownership check → `403` si pertenece a otro usuario
- Solo actualiza los campos presentes en el body (exclude_none)
- Si `es_predeterminada=True` → aplicar RN-DI02

---

### PATCH /api/v1/direcciones/{id}/predeterminada

Marcar una dirección como la dirección predeterminada del usuario.

**Auth**: Bearer JWT
**Response**: `200 OK` con `DireccionResponse`

**Reglas**:
- RN-DI03: ownership check → `403`
- RN-DI02: antes de marcar la nueva, hacer `UPDATE SET es_predeterminada=False` en TODAS las demás direcciones activas del usuario

---

### DELETE /api/v1/direcciones/{id}

Soft-delete de una dirección del usuario autenticado.

**Auth**: Bearer JWT
**Response**: `204 No Content`

**Reglas**:
- RN-DI03: ownership check → `403`
- Soft delete: setear `eliminado_en=datetime.utcnow()`
- Si la dirección eliminada era `es_predeterminada=True` → asignar `es_predeterminada=True` a la más reciente restante (por `creado_en DESC`)
- Si no hay más direcciones activas → no hacer nada (ninguna predeterminada)

---

## Reglas de Negocio

| ID | Regla | Implementación |
|----|-------|---------------|
| RN-DI01 | Primera dirección del usuario → auto-predeterminada | `count_active_by_usuario == 0` antes de crear → forzar `es_predeterminada=True` |
| RN-DI02 | Solo una predeterminada por usuario | `unset_predeterminada_for_usuario(usuario_id)` antes de marcar nueva |
| RN-DI03 | Ownership por `usuario_id` del JWT | `if direccion.usuario_id != usuario_id: raise 403` en service |

## Campos del Modelo

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | int | PK autoincrement |
| `usuario_id` | int | FK a usuarios.id, del JWT |
| `alias` | str | max 100 chars, sanitizado XSS |
| `linea1` | str | max 255 chars, sanitizado XSS |
| `piso` | str? | opcional |
| `departamento` | str? | opcional |
| `ciudad` | str | max 100 chars |
| `codigo_postal` | str | 4-10 chars |
| `referencia` | str? | max 255 chars, sanitizado XSS |
| `es_predeterminada` | bool | default False, solo una True por usuario |
| `creado_en` | datetime | auto |
| `actualizado_en` | datetime | auto, actualizar en cada update |
| `eliminado_en` | datetime? | soft delete, null = activo |

## Errores RFC 7807

Todos los errores siguen el formato RFC 7807:

```json
{
  "type": "about:blank",
  "title": "Not Found",
  "status": 404,
  "detail": "Direccion 99 not found"
}
```

| Status | Título | Cuándo |
|--------|--------|--------|
| 401 | Unauthorized | Token JWT ausente o inválido |
| 403 | Forbidden | La dirección pertenece a otro usuario (RN-DI03) |
| 404 | Not Found | Dirección no existe o fue soft-deleted |
| 204 | — | Delete exitoso (sin body) |

## Índice de Performance

```sql
CREATE INDEX CONCURRENTLY idx_direcciones_entrega_usuario
ON direcciones_entrega(usuario_id)
WHERE eliminado_en IS NULL;
```

Mejora los queries de listado y conteo por usuario.
