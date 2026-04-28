# Idempotent Seed Data Script

## Overview

Automated test data initialization ensures all developers and CI/CD pipelines have consistent reference data (Roles, OrderStates, PaymentMethods, admin user) in the database. The script must be **idempotent**: running it multiple times produces the same result without duplicates or errors.

## Functional Requirements

1. **Roles (4 static)**:
   - `ADMIN`: Full system access
   - `STOCK`: Product inventory management
   - `PEDIDOS`: Order workflow management
   - `CLIENT`: End user, customer

   Must check for existence before INSERT (no duplicates on re-run).

2. **Order States (6 static)**:
   - `PENDIENTE`: Order created, awaiting confirmation
   - `CONFIRMADO`: Order confirmed, payment processed
   - `EN_PREPARACIÓN`: Kitchen/warehouse preparing order
   - `EN_CAMINO`: Order in transit (delivery)
   - `ENTREGADO`: Order delivered to customer
   - `CANCELADO`: Order cancelled (reachable from any pre-terminal state)

3. **Payment Methods (3 static)**:
   - `MERCADOPAGO`: MercadoPago Checkout integration
   - `EFECTIVO`: Cash on delivery
   - `TRANSFERENCIA`: Bank transfer

4. **Admin User (1 seeded)**:
   - Email: `admin@foodstore.com`
   - Password: `Admin123!` (hashed with bcrypt)
   - Role: `ADMIN`
   - Timestamps: `creado_en`, `actualizado_en` set to current time

## Non-Functional Requirements

1. **Idempotency**: Safe to run multiple times without duplicate errors or data corruption
   - Use `SELECT ... WHERE ... LIMIT 1` to check existence before INSERT
   - Or use database UNIQUE constraints and handle conflicts gracefully

2. **Error Handling**: Clear error messages if seed fails (e.g., database unreachable)
   - Log each step: "Seeding Roles... ✓", "Seeding OrderStates... ✓"
   - Exit with status 1 if critical failure

3. **Type Safety**: Use SQLModel + Python type hints, avoid raw SQL

4. **Logging**: Print progress to console
   - "Seeding database..."
   - "Roles: 4 rows (or already exist)"
   - "OrderStates: 6 rows (or already exist)"
   - etc.

5. **Environment**: Works with Docker or native PostgreSQL
   - Only requirement: `DATABASE_URL` environment variable set
   - Should not hardcode hostname/port

## API / Interface

### Command Line

```bash
# Run seed script
poetry run python backend/scripts/seed.py

# Expected output:
# Seeding database...
# ✓ Roles: 4 rows inserted (or already exist)
# ✓ OrderStates: 6 rows inserted (or already exist)
# ✓ PaymentMethods: 3 rows inserted (or already exist)
# ✓ Admin user: created (or already exists)
# Seed complete!
```

### Python Code (Implementation Pattern)

```python
# backend/scripts/seed.py
import asyncio
from sqlmodel import Session, select
from backend.core.database import async_session, engine
from backend.core.config import settings
from backend.core.security import hash_password
from backend.models import Rol, EstadoPedido, FormaPago, Usuario

async def seed_database():
    """Idempotent database seeding."""
    async with async_session() as session:
        
        # Seed Roles
        roles_data = [
            {"nombre": "ADMIN"},
            {"nombre": "STOCK"},
            {"nombre": "PEDIDOS"},
            {"nombre": "CLIENT"},
        ]
        for role_data in roles_data:
            existing = await session.exec(
                select(Rol).where(Rol.nombre == role_data["nombre"]).limit(1)
            )
            if not existing.first():
                session.add(Rol(**role_data))
        
        # Seed OrderStates
        # Seed PaymentMethods
        # Seed Admin User
        
        await session.commit()
        print("✓ Seed complete!")

if __name__ == "__main__":
    asyncio.run(seed_database())
```

## Acceptance Criteria

- [ ] Script location: `backend/scripts/seed.py` exists
- [ ] Executable: `poetry run python backend/scripts/seed.py` succeeds
- [ ] Creates 4 Roles: ADMIN, STOCK, PEDIDOS, CLIENT (verify in database)
- [ ] Creates 6 OrderStates: PENDIENTE, CONFIRMADO, EN_PREPARACIÓN, EN_CAMINO, ENTREGADO, CANCELADO
- [ ] Creates 3 PaymentMethods: MERCADOPAGO, EFECTIVO, TRANSFERENCIA
- [ ] Creates 1 admin user: admin@foodstore.com with ADMIN role and hashed password
- [ ] Idempotent: Run script twice, second run reports "already exist" (no errors, no duplicates)
- [ ] Error handling: If database unreachable, script exits with clear error message
- [ ] Logging: Prints progress to console with ✓ marks
- [ ] Works with Docker PostgreSQL: After `docker-compose up -d`, script succeeds
- [ ] Works with native PostgreSQL: After configuring `.env.local`, script succeeds
