# RBAC Factory Capability

## Overview

Factory function that creates role-based access control dependencies for protecting FastAPI routes. Validates current user has at least one required role.

## ADDED Requirements

#### Scenario: Route protected by single role
```python
@app.post("/api/v1/productos")
async def create_product(
    data: CreateProductRequest,
    current_user: Usuario = Depends(get_current_user),
    _ = Depends(require_role(["ADMIN", "STOCK"]))
):
    # Only users with ADMIN or STOCK role reach here
    # If user lacks both roles: 403 Forbidden
    pass
```

#### Scenario: Route protected by multiple roles
```python
@app.get("/api/v1/admin/metricas")
async def get_metrics(
    current_user: Usuario = Depends(get_current_user),
    _ = Depends(require_role(["ADMIN"]))
):
    # Only ADMIN users can access
    pass
```

#### Scenario: Check role in handler (alternative)
```python
@app.patch("/api/v1/pedidos/:id")
async def transition_order_state(
    order_id: int,
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol.nombre not in ["ADMIN", "PEDIDOS"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    # ... rest of logic
```

## Requirements

### R1: Factory Function Signature
- Function: `def require_role(roles: list[str]) -> Callable`
  - Input: list of allowed role names (e.g., ["ADMIN", "STOCK"])
  - Output: async callable dependency
  - Example: `require_role(["ADMIN", "STOCK"])` returns a dependency

### R2: Dependency Implementation
- Internal async function that takes `current_user: Usuario = Depends(get_current_user)`
- Compares `current_user.rol.nombre` against allowed roles list
- Case-insensitive or exact match (define behavior)
- Returns None (dependencies don't return values, just pass/fail)

### R3: Role Validation
- Raises `HTTPException(status_code=403, detail="Insufficient permissions")`
  - If user role not in allowed list
  - If user has no role (unlikely but handle gracefully)
  - If user's role is NULL (soft-deleted or corrupted data)

### R4: Multiple Role Support
- Accept list of roles: `["ADMIN", "STOCK", "PEDIDOS"]`
- User needs at least ONE of the listed roles (OR logic, not AND)

### R5: Role Lookup
- Assume `current_user.rol` is already loaded (from CHANGE 3 FK relationship)
- Access role name via `current_user.rol.nombre`
- No additional database queries needed

### R6: Error Response
- HTTP 403 Forbidden
- JSON body: `{"detail": "Insufficient permissions"}`
- No stack trace or sensitive info in response

## Acceptance Criteria

- [ ] `require_role(roles: list[str])` factory created
- [ ] Returns async callable dependency
- [ ] Checks current_user.rol.nombre against roles list
- [ ] Raises 403 if role not allowed
- [ ] Works with single and multiple roles
- [ ] Integrates with FastAPI's Depends()
- [ ] All future protected routes use this pattern
