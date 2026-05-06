#!/usr/bin/env python
"""
Verification script for backend-postgres-alembic-seed implementation.

This script performs comprehensive checks to ensure all models, migrations,
and seed logic are correctly implemented without requiring a running database.

Usage:
    python backend/scripts/verify.py

Exit codes:
    0 = All checks passed
    1 = One or more checks failed
"""

import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


def print_header(title):
    """Print formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_check(name, status, details=""):
    """Print check result."""
    icon = "[OK]" if status else "[FAIL]"
    result = "PASS" if status else "FAIL"
    print(f"  {icon} {name:50} {result}")
    if details:
        print(f"      {details}")
    return status


def verify_imports():
    """Verify all models can be imported."""
    print_header("1. Model Imports")
    
    try:
        from core.models import (
            Rol, EstadoPedido, FormaPago, Usuario, RefreshToken,
            DireccionEntrega, Categoria, Producto, Ingrediente,
            ProductoCategoria, ProductoIngrediente, Pedido,
            DetallePedido, HistorialEstadoPedido, Pago
        )
        print_check("Import all 15 models", True)
        return True
    except Exception as e:
        print_check("Import all 15 models", False, str(e))
        return False


def verify_metadata():
    """Verify SQLModel metadata registration."""
    print_header("2. SQLModel Metadata Registration")
    
    try:
        from sqlmodel import SQLModel
        # Import all models to register them with metadata
        import core.models  # noqa: F401
        
        tables = list(SQLModel.metadata.tables.keys())
        expected_tables = {
            'roles', 'estados_pedido', 'formas_pago',
            'usuarios', 'refresh_tokens', 'direcciones_entrega',
            'categorias', 'productos', 'ingredientes',
            'producto_categoria', 'producto_ingrediente',
            'pedidos', 'detalle_pedido', 'historial_estado_pedido', 'pagos'
        }
        
        actual_set = set(tables)
        missing = expected_tables - actual_set
        extra = actual_set - expected_tables
        
        if not missing and not extra:
            print_check(f"Table count: {len(tables)}/15", True)
            for table in sorted(tables):
                print(f"      - {table}")
            return True
        else:
            if missing:
                print_check(f"Missing tables: {missing}", False)
            if extra:
                print_check(f"Extra tables: {extra}", False)
            return False
            
    except Exception as e:
        print_check("SQLModel metadata", False, str(e))
        return False


def verify_model_fields():
    """Verify all models have required fields."""
    print_header("3. Model Fields Verification")
    
    from sqlalchemy import inspect
    # Import all models to register them
    import core.models  # noqa: F401
    from core.models import (
        Rol, EstadoPedido, FormaPago, Usuario, RefreshToken,
        DireccionEntrega, Categoria, Producto, Ingrediente,
        ProductoCategoria, ProductoIngrediente, Pedido,
        DetallePedido, HistorialEstadoPedido, Pago
    )
    
    model_requirements = {
        'Rol': ['id', 'nombre', 'descripcion', 'creado_en'],
        'EstadoPedido': ['id', 'nombre', 'descripcion', 'creado_en'],
        'FormaPago': ['id', 'nombre', 'descripcion', 'activo', 'creado_en'],
        'Usuario': ['id', 'email', 'hashed_password', 'nombre', 'rol_id', 
                   'creado_en', 'actualizado_en', 'eliminado_en'],
        'RefreshToken': ['id', 'usuario_id', 'token', 'expires_at', 
                        'revoked_at', 'creado_en'],
        'DireccionEntrega': ['id', 'usuario_id', 'alias', 'linea1', 'ciudad',
                            'codigo_postal', 'creado_en', 'actualizado_en', 'eliminado_en'],
        'Categoria': ['id', 'nombre', 'padre_id', 'creado_en', 
                     'actualizado_en', 'eliminado_en'],
        'Producto': ['id', 'nombre', 'precio_base', 'stock_cantidad', 'disponible',
                    'creado_en', 'actualizado_en', 'eliminado_en'],
        'Ingrediente': ['id', 'nombre', 'es_alergeno', 'creado_en'],
        'Pedido': ['id', 'usuario_id', 'estado_pedido_id', 'total',
                  'creado_en', 'actualizado_en', 'eliminado_en'],
        'DetallePedido': ['id', 'pedido_id', 'producto_id', 'cantidad',
                         'precio_snapshot', 'nombre_snapshot', 'creado_en'],
        'HistorialEstadoPedido': ['id', 'pedido_id', 'estado_nuevo_id', 'creado_en'],
        'Pago': ['id', 'pedido_id', 'idempotency_key', 'creado_en',
                'actualizado_en', 'eliminado_en'],
    }
    
    model_map = {
        'Rol': Rol,
        'EstadoPedido': EstadoPedido,
        'FormaPago': FormaPago,
        'Usuario': Usuario,
        'RefreshToken': RefreshToken,
        'DireccionEntrega': DireccionEntrega,
        'Categoria': Categoria,
        'Producto': Producto,
        'Ingrediente': Ingrediente,
        'Pedido': Pedido,
        'DetallePedido': DetallePedido,
        'HistorialEstadoPedido': HistorialEstadoPedido,
        'Pago': Pago,
    }
    
    all_pass = True
    
    for model_name, required_fields in sorted(model_requirements.items()):
        try:
            model = model_map[model_name]
            mapper = inspect(model)
            actual_fields = {c.key for c in mapper.columns}
            
            missing = set(required_fields) - actual_fields
            if missing:
                print_check(f"{model_name:20}", False, f"Missing: {missing}")
                all_pass = False
            else:
                print_check(f"{model_name:20}", True)
        except Exception as e:
            print_check(f"{model_name:20}", False, str(e))
            all_pass = False
    
    return all_pass


def verify_audit_fields():
    """Verify audit fields are properly configured."""
    print_header("4. Audit Fields Configuration")
    
    from sqlalchemy import inspect
    from core.models import (
        Usuario, DireccionEntrega, Categoria, Producto, Pedido, Pago,
        Rol, EstadoPedido, FormaPago, RefreshToken,
        ProductoCategoria, ProductoIngrediente, HistorialEstadoPedido
    )
    
    # Entities that should have soft delete
    soft_delete_entities = [
        ('Usuario', Usuario), ('DireccionEntrega', DireccionEntrega),
        ('Categoria', Categoria), ('Producto', Producto),
        ('Pedido', Pedido), ('Pago', Pago)
    ]
    
    # Entities that should NOT have soft delete
    no_soft_delete_entities = [
        ('Rol', Rol), ('EstadoPedido', EstadoPedido), ('FormaPago', FormaPago),
        ('RefreshToken', RefreshToken),
        ('ProductoCategoria', ProductoCategoria),
        ('ProductoIngrediente', ProductoIngrediente),
        ('HistorialEstadoPedido', HistorialEstadoPedido)
    ]
    
    # Entities that should have updatable timestamps (actualizado_en)
    updatable_ts_entities = [
        ('Usuario', Usuario), ('DireccionEntrega', DireccionEntrega),
        ('Categoria', Categoria), ('Producto', Producto), ('Pedido', Pedido),
        ('Pago', Pago)
    ]
    
    all_pass = True
    
    # Check soft delete entities
    for entity_name, entity in soft_delete_entities:
        mapper = inspect(entity)
        fields = {c.key for c in mapper.columns}
        
        if 'eliminado_en' in fields:
            print_check(f"{entity_name:20} has eliminado_en", True)
        else:
            print_check(f"{entity_name:20} has eliminado_en", False)
            all_pass = False
    
    # Check entities without soft delete
    for entity_name, entity in no_soft_delete_entities:
        mapper = inspect(entity)
        fields = {c.key for c in mapper.columns}
        
        if 'eliminado_en' not in fields:
            print_check(f"{entity_name:20} no soft delete", True)
        else:
            print_check(f"{entity_name:20} no soft delete", False)
            all_pass = False
    
    # Check updatable timestamp entities
    for entity_name, entity in updatable_ts_entities:
        mapper = inspect(entity)
        fields = {c.key for c in mapper.columns}
        
        if 'actualizado_en' in fields:
            print_check(f"{entity_name:20} has actualizado_en", True)
        else:
            print_check(f"{entity_name:20} has actualizado_en", False)
            all_pass = False
    
    return all_pass


def verify_migration():
    """Verify migration file is complete."""
    print_header("5. Alembic Migration File")
    
    import re
    
    migration_path = backend_path / "alembic/versions/001_initial_schema.py"
    
    if not migration_path.exists():
        print_check("Migration file exists", False, f"Not found: {migration_path}")
        return False
    
    with open(migration_path, 'r') as f:
        content = f.read()
    
    all_pass = True
    
    # Check for CREATE TABLE statements
    create_count = len(re.findall(r'op\.create_table\(', content))
    expected_creates = 15
    all_pass &= print_check(f"CREATE TABLE statements", 
                            create_count == expected_creates,
                            f"Found: {create_count}, Expected: {expected_creates}")
    
    # Check for DROP TABLE statements in downgrade
    drop_count = len(re.findall(r"op\.drop_table\(", content))
    all_pass &= print_check(f"DROP TABLE statements",
                           drop_count == expected_creates,
                           f"Found: {drop_count}, Expected: {expected_creates}")
    
    # Check naming conventions
    fk_count = len(re.findall(r"name='fk_", content))
    all_pass &= print_check(f"Foreign Key constraints (fk_*)",
                           fk_count > 0, f"Found: {fk_count}")
    
    pk_count = len(re.findall(r"name='pk_", content))
    all_pass &= print_check(f"Primary Key constraints (pk_*)",
                           pk_count > 0, f"Found: {pk_count}")
    
    # Check for upgrade/downgrade functions
    has_upgrade = 'def upgrade()' in content
    has_downgrade = 'def downgrade()' in content
    all_pass &= print_check("Has upgrade() function", has_upgrade)
    all_pass &= print_check("Has downgrade() function", has_downgrade)
    
    return all_pass


def verify_seed_script():
    """Verify seed script is complete."""
    print_header("6. Seed Script Verification")
    
    import re
    
    seed_path = backend_path / "scripts/seed.py"
    
    if not seed_path.exists():
        print_check("Seed script exists", False, f"Not found: {seed_path}")
        return False
    
    with open(seed_path, 'r') as f:
        content = f.read()
    
    all_pass = True
    
    # Check for get_or_create functions
    functions = [
        'get_or_create_rol',
        'get_or_create_estado_pedido',
        'get_or_create_forma_pago',
        'get_or_create_usuario',
        'seed_database'
    ]
    
    for func in functions:
        all_pass &= print_check(f"Has {func}()", func in content)
    
    # Check for seed data
    seed_data = {
        'ADMIN': 'ADMIN role',
        'STOCK': 'STOCK role',
        'PEDIDOS': 'PEDIDOS role',
        'CLIENT': 'CLIENT role',
        'PENDIENTE': 'PENDIENTE state',
        'CONFIRMADO': 'CONFIRMADO state',
        'EN_PREPARACI': 'PREPARATION state (EN_PREPARACI*)',  # Unicode safe
        'ENTREGADO': 'ENTREGADO state',
        'CANCELADO': 'CANCELADO state',
        'MERCADOPAGO': 'MERCADOPAGO payment',
        'EFECTIVO': 'EFECTIVO payment',
        'TRANSFERENCIA': 'TRANSFERENCIA payment',
        'admin@foodstore.com': 'Admin user',
    }
    
    for data, description in seed_data.items():
        all_pass &= print_check(f"Seeds {description}", data in content)
    
    # Check for async/await
    has_async = 'async def' in content
    all_pass &= print_check("Uses async functions", has_async)
    
    # Check for AsyncSession
    has_async_session = 'AsyncSession' in content
    all_pass &= print_check("Uses AsyncSession", has_async_session)
    
    return all_pass


def verify_database_config():
    """Verify database configuration files."""
    print_header("7. Database Configuration Files")
    
    all_pass = True
    
    # Check .env file
    env_path = backend_path / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.read()
        all_pass &= print_check(".env file exists", True)
        all_pass &= print_check(".env has DATABASE_URL", "DATABASE_URL" in env_content)
        all_pass &= print_check(".env has SECRET_KEY", "SECRET_KEY" in env_content)
    else:
        all_pass &= print_check(".env file exists", False)
    
    # Check alembic.ini
    alembic_ini = backend_path / "alembic.ini"
    if alembic_ini.exists():
        all_pass &= print_check("alembic.ini exists", True)
    else:
        all_pass &= print_check("alembic.ini exists", False)
    
    # Check docker-compose.yml
    docker_compose = backend_path.parent / "docker-compose.yml"
    if docker_compose.exists():
        with open(docker_compose, 'r') as f:
            dc_content = f.read()
        all_pass &= print_check("docker-compose.yml exists", True)
        all_pass &= print_check("Defines PostgreSQL service", "postgres:" in dc_content)
        all_pass &= print_check("Has postgres_data volume", "postgres_data:" in dc_content)
    else:
        all_pass &= print_check("docker-compose.yml exists", False)
    
    return all_pass


def verify_password_hashing():
    """Verify password hashing is configured."""
    print_header("8. Security: Password Hashing")
    
    from core.models import Usuario
    import inspect as py_inspect
    
    all_pass = True
    
    # Check hash_password static method exists
    all_pass &= print_check("Usuario.hash_password() exists",
                           hasattr(Usuario, 'hash_password'))
    
    # Check verify_password instance method exists
    all_pass &= print_check("Usuario.verify_password() exists",
                           hasattr(Usuario, 'verify_password'))
    
    # Check pwd_context is configured
    try:
        from core.models import pwd_context
        all_pass &= print_check("pwd_context configured", True)
    except:
        all_pass &= print_check("pwd_context configured", False)
    
    return all_pass


def main():
    """Run all verifications."""
    print("\n" + "="*70)
    print("  Food Store Database Implementation Verification")
    print("="*70)
    print(f"  Timestamp: {datetime.now().isoformat()}")
    print(f"  Backend Path: {backend_path}")
    
    results = []
    
    try:
        results.append(("Model Imports", verify_imports()))
        results.append(("Metadata Registration", verify_metadata()))
        results.append(("Model Fields", verify_model_fields()))
        results.append(("Audit Fields", verify_audit_fields()))
        results.append(("Migration File", verify_migration()))
        results.append(("Seed Script", verify_seed_script()))
        results.append(("Database Config", verify_database_config()))
        results.append(("Password Hashing", verify_password_hashing()))
    except Exception as e:
        print(f"\n[ERROR] Verification failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Print summary
    print_header("SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        icon = "[OK]" if result else "[FAIL]"
        status = "PASS" if result else "FAIL"
        print(f"  {icon} {name:40} {status}")
    
    print()
    print(f"  Total: {passed}/{total} sections passed")
    
    if passed == total:
        print("\n  All verification checks PASSED! Implementation is correct.")
        print("="*70 + "\n")
        return 0
    else:
        print(f"\n  {total - passed} check(s) FAILED. Please review above.")
        print("="*70 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
