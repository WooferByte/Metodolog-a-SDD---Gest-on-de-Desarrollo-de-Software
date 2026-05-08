"""
Unit tests for backend/pedidos/schemas.py — DetallePedidoCreate, PedidoCreate.
"""
import pytest
from pydantic import ValidationError

from pedidos.schemas import DetallePedidoCreate, PedidoCreate


class TestDetallePedidoCreate:
    """Tests for DetallePedidoCreate schema."""

    def test_valid_item(self):
        """Valid producto_id and cantidad >= 1 should be accepted."""
        item = DetallePedidoCreate(producto_id=1, cantidad=2)
        assert item.producto_id == 1
        assert item.cantidad == 2

    def test_zero_cantidad_rejected(self):
        """cantidad = 0 should raise ValidationError (ge=1)."""
        with pytest.raises(ValidationError) as exc_info:
            DetallePedidoCreate(producto_id=1, cantidad=0)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("cantidad",) for e in errors)

    def test_negative_cantidad_rejected(self):
        """Negative cantidad should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            DetallePedidoCreate(producto_id=1, cantidad=-5)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("cantidad",) for e in errors)

    def test_optional_ingredientes_excluidos_defaults_none(self):
        """ingredientes_excluidos should default to None."""
        item = DetallePedidoCreate(producto_id=1, cantidad=1)
        assert item.ingredientes_excluidos is None

    def test_ingredientes_excluidos_list(self):
        """ingredientes_excluidos accepts a list of ints."""
        item = DetallePedidoCreate(producto_id=1, cantidad=1, ingredientes_excluidos=[2, 3])
        assert item.ingredientes_excluidos == [2, 3]


class TestPedidoCreate:
    """Tests for PedidoCreate schema."""

    def _valid_item(self):
        return {"producto_id": 1, "cantidad": 1}

    def test_valid_order(self):
        """Valid order with at least one item should be accepted."""
        order = PedidoCreate(
            direccion_entrega_id=1,
            forma_pago_id=1,
            items=[self._valid_item()],
        )
        assert len(order.items) == 1

    def test_empty_items_rejected(self):
        """items list must have at least one item (min_length=1)."""
        with pytest.raises(ValidationError) as exc_info:
            PedidoCreate(
                direccion_entrega_id=1,
                forma_pago_id=1,
                items=[],
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("items",) for e in errors)

    def test_observacion_sanitized(self):
        """HTML tags in observacion should be stripped."""
        order = PedidoCreate(
            direccion_entrega_id=1,
            forma_pago_id=1,
            items=[self._valid_item()],
            observacion="<script>evil()</script>Sin cebolla",
        )
        assert order.observacion == "Sin cebolla"

    def test_observacion_too_long_rejected(self):
        """observacion longer than 500 chars should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            PedidoCreate(
                direccion_entrega_id=1,
                forma_pago_id=1,
                items=[self._valid_item()],
                observacion="x" * 501,
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("observacion",) for e in errors)

    def test_none_observacion_accepted(self):
        """observacion is optional — defaults to None."""
        order = PedidoCreate(
            direccion_entrega_id=1,
            forma_pago_id=1,
            items=[self._valid_item()],
        )
        assert order.observacion is None

    def test_multiple_items_accepted(self):
        """Multiple items in one order should all be validated."""
        order = PedidoCreate(
            direccion_entrega_id=1,
            forma_pago_id=1,
            items=[
                {"producto_id": 1, "cantidad": 2},
                {"producto_id": 3, "cantidad": 1},
            ],
        )
        assert len(order.items) == 2
