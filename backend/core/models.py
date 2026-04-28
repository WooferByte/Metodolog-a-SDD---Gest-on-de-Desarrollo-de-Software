"""
SQLModel domain models for the Food Store application.

Models use SQLModel which combines SQLAlchemy ORM capabilities with Pydantic validation.
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
    - rol_id: Foreign key to Rol table
    - activo: Account status
    """
    __tablename__ = "usuarios"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    nombre: str = Field(max_length=100)
    apellido: Optional[str] = Field(default=None, max_length=100)
    rol_id: Optional[int] = Field(default=None, foreign_key="roles.id")
    activo: bool = Field(default=True)
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for secure storage."""
        return pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        return pwd_context.verify(password, self.hashed_password)
