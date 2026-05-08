"""
Unit tests for backend/productos/schemas.py — ProductoCreate, ProductoUpdate, ProductoResponse.
"""
from decimal import Decimal

import pytest
from pydantic import ValidationError

from productos.schemas import ProductoCreate, ProductoUpdate, ProductoResponse


class TestProductoCreate:
    """Tests for ProductoCreate schema."""

    def test_valid_product(self):
        """Valid fields should be accepted."""
        p = ProductoCreate(nombre="Pizza", precio_base=Decimal("12.50"), stock_cantidad=10)
        assert p.nombre == "Pizza"
        assert p.precio_base == Decimal("12.50")
        assert p.stock_cantidad == 10
        assert p.disponible is True

    def test_negative_price_rejected(self):
        """precio_base <= 0 should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ProductoCreate(nombre="X", precio_base=Decimal("-5"), stock_cantidad=0)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("precio_base",) for e in errors)

    def test_zero_price_rejected(self):
        """precio_base = 0 should raise ValidationError (gt=0)."""
        with pytest.raises(ValidationError) as exc_info:
            ProductoCreate(nombre="X", precio_base=Decimal("0"), stock_cantidad=0)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("precio_base",) for e in errors)

    def test_negative_stock_rejected(self):
        """Negative stock_cantidad should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ProductoCreate(nombre="X", precio_base=Decimal("1"), stock_cantidad=-1)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("stock_cantidad",) for e in errors)

    def test_zero_stock_accepted(self):
        """stock_cantidad = 0 is valid (ge=0)."""
        p = ProductoCreate(nombre="X", precio_base=Decimal("1"), stock_cantidad=0)
        assert p.stock_cantidad == 0

    def test_empty_nombre_rejected(self):
        """Empty nombre should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ProductoCreate(nombre="", precio_base=Decimal("1"), stock_cantidad=0)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("nombre",) for e in errors)

    def test_nombre_sanitized_script_tag(self):
        """Script tag in nombre should be stripped by XSS sanitizer."""
        p = ProductoCreate(
            nombre="<script>alert(1)</script>Pizza",
            precio_base=Decimal("10"),
            stock_cantidad=5,
        )
        assert p.nombre == "Pizza"

    def test_descripcion_sanitized(self):
        """HTML in descripcion should be stripped."""
        p = ProductoCreate(
            nombre="Pizza",
            precio_base=Decimal("10"),
            stock_cantidad=5,
            descripcion="<b>Deliciosa</b> pizza",
        )
        assert p.descripcion == "Deliciosa pizza"

    def test_none_descripcion_accepted(self):
        """Optional descripcion defaults to None."""
        p = ProductoCreate(nombre="Pizza", precio_base=Decimal("10"), stock_cantidad=5)
        assert p.descripcion is None


class TestProductoUpdate:
    """Tests for ProductoUpdate schema (all fields optional)."""

    def test_partial_update_no_fields(self):
        """Empty update is valid — all fields optional."""
        p = ProductoUpdate()
        assert p.nombre is None
        assert p.precio_base is None

    def test_negative_price_rejected_in_update(self):
        """Negative price should still be rejected in update."""
        with pytest.raises(ValidationError):
            ProductoUpdate(precio_base=Decimal("-1"))

    def test_nombre_sanitized_in_update(self):
        """XSS sanitization should apply in update too."""
        p = ProductoUpdate(nombre="<i>test</i>")
        assert p.nombre == "test"
