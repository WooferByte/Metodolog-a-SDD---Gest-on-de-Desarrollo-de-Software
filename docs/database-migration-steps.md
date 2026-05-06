# FoodStore PostgreSQL Migration - CHANGE 3

## Current Status

**COMPLETED:**
- Alembic initialized
- All 15 SQLModel entities defined in `backend/core/models.py`
- Migration file created: `backend/alembic/versions/001_initial_schema.py`
- Database configuration set in `backend/alembic.ini`
- Async SQLAlchemy env.py configured

## Next Steps (PHASE 4 & 5)

### Step 1: Start PostgreSQL
```bash
# From project root directory
docker-compose up -d

# Verify PostgreSQL is running
docker-compose ps
```

### Step 2: Apply Migration
```bash
cd backend
alembic upgrade head
```

### Step 3: Verify Schema Creation
```bash
docker exec -it foodstore-postgres psql -U postgres -d foodstore_db
\dt
```

### Step 4: Run Seed Script
```bash
cd backend
python scripts/seed.py
```

### Step 5: Verify Seed Data
```bash
docker exec -it foodstore-postgres psql -U postgres -d foodstore_db
SELECT * FROM roles;
SELECT id, email, nombre, rol_id FROM usuarios WHERE eliminado_en IS NULL;
```

## Table Mapping

All 15 tables created:
1. roles
2. estados_pedido
3. formas_pago
4. usuarios (with eliminado_en for soft delete)
5. refresh_tokens
6. direcciones_entrega (with soft delete)
7. categorias (hierarchical with padre_id, with soft delete)
8. productos (with soft delete)
9. ingredientes
10. producto_categoria (N:M pivot)
11. producto_ingrediente (N:M pivot with es_removible)
12. pedidos (with soft delete)
13. detalle_pedido
14. historial_estado_pedido (append-only, no soft delete)
15. pagos (with soft delete)

## Key Features Implemented

- Soft delete pattern with eliminado_en timestamp
- Proper foreign key constraints (CASCADE vs RESTRICT)
- Composite primary keys for pivot tables
- Index creation for frequently queried columns
- Audit fields (creado_en, actualizado_en)
- Naming conventions for constraints (FK, PK, IX, UQ)
- Decimal fields for monetary values
- JSON fields for flexible data (ingredientes_excluidos, gateway_response)

## Verification Commands

### Soft Deletes
```sql
UPDATE usuarios SET eliminado_en = NOW() WHERE email = 'admin@foodstore.com';
SELECT * FROM usuarios WHERE eliminado_en IS NULL;
```

### FK Constraints
```sql
-- This should fail
INSERT INTO pedidos (usuario_id, direccion_entrega_id, forma_pago_id, estado_pedido_id, total)
VALUES (999, 1, 1, 1, 100.00);
```

### Idempotency
```bash
python scripts/seed.py  # Run twice, should show [EXISTS] entries
```

## Git Commit

```bash
git commit -m "feat(backend): implement PostgreSQL schema with Alembic migrations and seed data (CHANGE 3)"
```
