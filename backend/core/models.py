"""
SQLModel domain models for the Food Store application.

Models use SQLModel which combines SQLAlchemy ORM capabilities with Pydantic validation.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UsuarioRol(SQLModel, table=True):
    """
    N:M pivot table for Usuario-Rol relationships.

    Allows users to have multiple roles (ERD v5).
    """
    __tablename__ = "usuario_rol"

    usuario_id: Optional[int] = Field(default=None, foreign_key="usuarios.id", primary_key=True)
    rol_id: Optional[int] = Field(default=None, foreign_key="roles.id", primary_key=True)


class Rol(SQLModel, table=True):
    """
    Role entity for role-based access control (RBAC).

    Roles:
    - ADMIN: Full system access
    - STOCK: Stock/inventory management
    - PEDIDOS: Orders management
    - CLIENT: Customer account
    """
    __tablename__ = "roles"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True, index=True, max_length=50)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    creado_en: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    usuarios: List["Usuario"] = Relationship(back_populates="roles", link_model=UsuarioRol)


class EstadoPedido(SQLModel, table=True):
    """
    Order status entity for order lifecycle management.
    
    Estados:
    - PENDIENTE: Order created, awaiting confirmation
    - CONFIRMADO: Order confirmed
    - EN_PREPARACIÓN: Being prepared in warehouse
    - EN_CAMINO: Out for delivery
    - ENTREGADO: Successfully delivered
    - CANCELADO: Order cancelled
    """
    __tablename__ = "estados_pedido"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True, index=True, max_length=50)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    creado_en: datetime = Field(default_factory=datetime.utcnow)


class FormaPago(SQLModel, table=True):
    """
    Payment method entity for payment processing.
    
    Métodos:
    - MERCADOPAGO: MercadoPago integration
    - EFECTIVO: Cash payment
    - TRANSFERENCIA: Bank transfer
    """
    __tablename__ = "formas_pago"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True, index=True, max_length=50)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    activo: bool = Field(default=True)
    creado_en: datetime = Field(default_factory=datetime.utcnow)


class Usuario(SQLModel, table=True):
    """
    User account entity for authentication and authorization.

    Fields:
    - email: Unique identifier
    - hashed_password: Bcrypt-hashed password (never store plain text)
    - nombre: User's display name
    - apellido: User's last name
    - activo: Account status
    - eliminado_en: Soft delete timestamp
    """
    __tablename__ = "usuarios"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    nombre: str = Field(max_length=100)
    apellido: Optional[str] = Field(default=None, max_length=100)
    activo: bool = Field(default=True)
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    eliminado_en: Optional[datetime] = None

    # Relationships — N:M via UsuarioRol pivot table
    roles: List["Rol"] = Relationship(back_populates="usuarios", link_model=UsuarioRol)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for secure storage."""
        return pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        return pwd_context.verify(password, self.hashed_password)


class RefreshToken(SQLModel, table=True):
    """
    Refresh token entity for JWT token refresh operations.
    
    Tracks issued refresh tokens with expiration and revocation support.
    """
    __tablename__ = "refresh_tokens"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuarios.id")
    token: str = Field(unique=True, index=True)
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    creado_en: datetime = Field(default_factory=datetime.utcnow)


class DireccionEntrega(SQLModel, table=True):
    """
    Delivery address entity for order fulfillment.
    
    Stores customer delivery addresses with soft delete support.
    """
    __tablename__ = "direcciones_entrega"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuarios.id")
    alias: str
    linea1: str
    piso: Optional[str] = None
    departamento: Optional[str] = None
    ciudad: str
    codigo_postal: str
    referencia: Optional[str] = None
    es_principal: bool = False
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    eliminado_en: Optional[datetime] = None


class Categoria(SQLModel, table=True):
    """
    Product category entity with hierarchical support.
    
    Supports parent-child relationships for category trees.
    """
    __tablename__ = "categorias"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True, index=True, max_length=255)
    descripcion: Optional[str] = None
    padre_id: Optional[int] = Field(default=None, foreign_key="categorias.id")
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    eliminado_en: Optional[datetime] = None


class Producto(SQLModel, table=True):
    """
    Product entity for store inventory.
    
    Stores product information including pricing, stock, and availability.
    """
    __tablename__ = "productos"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True, max_length=255)
    descripcion: Optional[str] = None
    precio_base: Decimal = Field(decimal_places=2, max_digits=10)
    stock_cantidad: int = 0
    disponible: bool = True
    imagen_url: Optional[str] = None
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    eliminado_en: Optional[datetime] = None


class Ingrediente(SQLModel, table=True):
    """
    Ingredient entity for product composition.
    
    Tracks ingredients with allergen information.
    """
    __tablename__ = "ingredientes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True, index=True, max_length=255)
    es_alergeno: bool = False
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    eliminado_en: Optional[datetime] = None


class ProductoCategoria(SQLModel, table=True):
    """
    N:M pivot table for Product-Category relationships.
    
    Allows products to belong to multiple categories.
    """
    __tablename__ = "producto_categoria"
    
    producto_id: int = Field(foreign_key="productos.id", primary_key=True)
    categoria_id: int = Field(foreign_key="categorias.id", primary_key=True)


class ProductoIngrediente(SQLModel, table=True):
    """
    N:M pivot table for Product-Ingredient relationships.
    
    Tracks product composition with removable ingredient flag.
    """
    __tablename__ = "producto_ingrediente"
    
    producto_id: int = Field(foreign_key="productos.id", primary_key=True)
    ingrediente_id: int = Field(foreign_key="ingredientes.id", primary_key=True)
    es_removible: bool = False


class Pedido(SQLModel, table=True):
    """
    Order entity for customer purchases.
    
    Tracks order state, payment, and delivery information.
    """
    __tablename__ = "pedidos"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuarios.id")
    direccion_entrega_id: int = Field(foreign_key="direcciones_entrega.id")
    forma_pago_id: int = Field(foreign_key="formas_pago.id")
    estado_pedido_id: int = Field(foreign_key="estados_pedido.id")
    total: Decimal = Field(decimal_places=2, max_digits=10)
    observacion: Optional[str] = None
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    eliminado_en: Optional[datetime] = None


class DetallePedido(SQLModel, table=True):
    """
    Order line item entity.
    
    Tracks individual products in orders with price and ingredient snapshots.
    """
    __tablename__ = "detalle_pedido"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: int = Field(foreign_key="pedidos.id")
    producto_id: int = Field(foreign_key="productos.id")
    cantidad: int
    precio_snapshot: Decimal = Field(decimal_places=2, max_digits=10)
    nombre_snapshot: str
    ingredientes_excluidos: Optional[str] = None  # JSON array as string
    creado_en: datetime = Field(default_factory=datetime.utcnow)


class HistorialEstadoPedido(SQLModel, table=True):
    """
    Append-only audit log for order status changes.
    
    Tracks all status transitions for orders (immutable).
    """
    __tablename__ = "historial_estado_pedido"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: int = Field(foreign_key="pedidos.id")
    estado_anterior_id: Optional[int] = Field(default=None, foreign_key="estados_pedido.id")
    estado_nuevo_id: int = Field(foreign_key="estados_pedido.id")
    observacion: Optional[str] = None
    usuario_responsable_id: Optional[int] = Field(default=None, foreign_key="usuarios.id")
    creado_en: datetime = Field(default_factory=datetime.utcnow)


class Pago(SQLModel, table=True):
    """
    Payment entity for order transactions.
    
    Tracks payments with MercadoPago integration and idempotency.
    """
    __tablename__ = "pagos"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: int = Field(foreign_key="pedidos.id")
    mp_payment_id: Optional[str] = Field(default=None, unique=True)
    mp_status: Optional[str] = None
    external_reference: str  # UUID
    idempotency_key: str = Field(unique=True)  # UUID
    gateway_response: Optional[str] = None  # JSON
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    eliminado_en: Optional[datetime] = None
