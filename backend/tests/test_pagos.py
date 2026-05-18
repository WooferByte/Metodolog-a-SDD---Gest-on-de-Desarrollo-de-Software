"""
Tests for payments-mercadopago-integration-backend change.

Strategy:
  - Unit tests using mocked UnitOfWork + repositories.
  - Covers crear_preferencia, procesar_webhook, get_pago_status.
  - Uses pytest + AsyncMock pattern consistent with the rest of the test suite.
  - MercadoPago SDK is always mocked (no real API calls).

Test coverage (10 tests):
  12.2  test_crear_preferencia_exitosa
  12.3  test_crear_preferencia_pedido_ajeno
  12.4  test_crear_preferencia_pedido_no_pendiente
  12.5  test_webhook_approved_actualiza_pago_y_pedido
  12.6  test_webhook_firma_invalida
  12.7  test_webhook_idempotente
  12.8  test_webhook_race_condition
  12.9  test_get_pago_status_exitoso
  12.10 test_get_pago_status_ajeno_forbidden
  Additional: test_crear_preferencia_pedido_not_found, test_confirmar_pedido_por_pago
"""
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from core.models import Pago, Pedido
from pagos import service as pagos_service
from pagos.model import PagoWebhookLog
from pagos.service import (
    crear_preferencia,
    get_pago_status,
    procesar_webhook,
    _validate_mp_signature,
)
from pedidos.service import confirmar_pedido_por_pago


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pedido(
    id: int = 100,
    usuario_id: int = 10,
    estado_pedido_id: int = 1,
    total: Decimal = Decimal("1500.00"),
    eliminado_en=None,
) -> MagicMock:
    """Build a mock Pedido."""
    p = MagicMock(spec=Pedido)
    p.id = id
    p.usuario_id = usuario_id
    p.estado_pedido_id = estado_pedido_id
    p.total = total
    p.eliminado_en = eliminado_en
    return p


def _make_pago(
    id: int = 1,
    pedido_id: int = 100,
    mp_payment_id: str = None,
    mp_status: str = "pending",
    preference_id: str = None,
    monto: Decimal = Decimal("1500.00"),
) -> MagicMock:
    """Build a mock Pago."""
    p = MagicMock(spec=Pago)
    p.id = id
    p.pedido_id = pedido_id
    p.mp_payment_id = mp_payment_id
    p.mp_status = mp_status
    p.preference_id = preference_id
    p.external_reference = str(pedido_id)
    p.idempotency_key = "test-key"
    p.creado_en = datetime.utcnow()
    p.actualizado_en = datetime.utcnow()
    p.eliminado_en = None
    return p


def _make_webhook_log(id: int = 1) -> MagicMock:
    """Build a mock PagoWebhookLog."""
    log = MagicMock(spec=PagoWebhookLog)
    log.id = id
    log.procesado = False
    log.error_msg = None
    return log


def _make_uow(
    pedido=None,
    pago=None,
    pago_by_mp_id=None,
    webhook_log=None,
) -> MagicMock:
    """Build a mock UnitOfWork for pagos tests."""
    uow = MagicMock()
    uow.session = AsyncMock()
    uow.session.add = MagicMock()
    uow.session.flush = AsyncMock()
    uow.session.rollback = AsyncMock()

    # pedidos repo
    pedidos_repo = AsyncMock()
    pedidos_repo.get_by_id = AsyncMock(return_value=pedido)
    pedidos_repo.update_estado = AsyncMock(return_value=pedido)
    uow.pedidos = pedidos_repo

    # pagos repo
    pagos_repo = AsyncMock()
    pagos_repo.get_by_pedido_id = AsyncMock(return_value=pago)
    pagos_repo.get_by_mercadopago_id = AsyncMock(return_value=pago_by_mp_id)
    pagos_repo.create = AsyncMock(return_value=pago or _make_pago())
    pagos_repo.update = AsyncMock(return_value=pago)
    uow.pagos = pagos_repo

    # webhook logs repo
    wh_log = webhook_log or _make_webhook_log()
    wh_repo = AsyncMock()
    wh_repo.create = AsyncMock(return_value=wh_log)
    uow.pago_webhook_logs = wh_repo

    # historial repo
    historial_repo = AsyncMock()
    historial_repo.append = AsyncMock()
    uow.historial_estado_pedido = historial_repo

    return uow


def _make_sdk(
    preference_response=None,
    payment_response=None,
    raise_on_preference=None,
    raise_on_payment=None,
) -> MagicMock:
    """Build a mock MercadoPago SDK."""
    sdk = MagicMock()

    # SDK.preference().create(...)
    pref_mock = MagicMock()
    if raise_on_preference:
        pref_mock.create = MagicMock(side_effect=raise_on_preference)
    else:
        pref_mock.create = MagicMock(
            return_value=preference_response
            or {
                "response": {
                    "id": "pref_TEST_123",
                    "init_point": "https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id=pref_TEST_123",
                }
            }
        )
    sdk.preference = MagicMock(return_value=pref_mock)

    # SDK.payment().get(...)
    pay_mock = MagicMock()
    if raise_on_payment:
        pay_mock.get = MagicMock(side_effect=raise_on_payment)
    else:
        pay_mock.get = MagicMock(
            return_value=payment_response
            or {
                "status": 200,
                "response": {
                    "id": "12345678",
                    "status": "approved",
                    "transaction_amount": 1500.0,
                    "external_reference": "100",
                },
            }
        )
    sdk.payment = MagicMock(return_value=pay_mock)

    return sdk


# ---------------------------------------------------------------------------
# Tests for crear_preferencia
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_crear_preferencia_exitosa():
    """Test 12.2 — Successful preference creation returns init_point and pago_id."""
    pedido = _make_pedido(id=100, usuario_id=10, estado_pedido_id=1)
    new_pago = _make_pago(id=42, pedido_id=100, preference_id="pref_TEST_123")
    uow = _make_uow(pedido=pedido)
    uow.pagos.create = AsyncMock(return_value=new_pago)
    sdk = _make_sdk()

    result = await crear_preferencia(
        pedido_id=100,
        usuario_id=10,
        sdk=sdk,
        uow=uow,
    )

    assert result.init_point.startswith("https://")
    assert result.preference_id == "pref_TEST_123"
    assert result.pago_id == 42
    uow.pagos.create.assert_called_once()


@pytest.mark.asyncio
async def test_crear_preferencia_pedido_not_found():
    """Test — 404 when pedido does not exist."""
    uow = _make_uow(pedido=None)
    sdk = _make_sdk()

    with pytest.raises(HTTPException) as exc_info:
        await crear_preferencia(pedido_id=999, usuario_id=10, sdk=sdk, uow=uow)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_crear_preferencia_pedido_ajeno():
    """Test 12.3 — 403 when pedido belongs to another user."""
    pedido = _make_pedido(id=100, usuario_id=99, estado_pedido_id=1)
    uow = _make_uow(pedido=pedido)
    sdk = _make_sdk()

    with pytest.raises(HTTPException) as exc_info:
        await crear_preferencia(
            pedido_id=100,
            usuario_id=10,  # different from pedido.usuario_id=99
            sdk=sdk,
            uow=uow,
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_crear_preferencia_pedido_no_pendiente():
    """Test 12.4 — 409 when pedido is not in PENDIENTE state."""
    pedido = _make_pedido(id=100, usuario_id=10, estado_pedido_id=2)  # CONFIRMADO
    uow = _make_uow(pedido=pedido)
    sdk = _make_sdk()

    with pytest.raises(HTTPException) as exc_info:
        await crear_preferencia(pedido_id=100, usuario_id=10, sdk=sdk, uow=uow)

    assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# Tests for procesar_webhook
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_webhook_approved_actualiza_pago_y_pedido():
    """
    Test 12.5 — Approved webhook triggers Pago update and pedido FSM transition.
    """
    pedido = _make_pedido(id=100, usuario_id=10, estado_pedido_id=1)
    log_entry = _make_webhook_log(id=5)
    uow = _make_uow(pedido=pedido, pago_by_mp_id=None, webhook_log=log_entry)
    uow.pago_webhook_logs.create = AsyncMock(return_value=log_entry)

    sdk = _make_sdk(
        payment_response={
            "status": 200,
            "response": {
                "id": "12345678",
                "status": "approved",
                "transaction_amount": 1500.0,
                "external_reference": "100",
            },
        }
    )

    payload = {"topic": "payment", "data": {"id": "12345678"}}

    with patch("pedidos.service.confirmar_pedido_por_pago", new_callable=AsyncMock) as mock_confirm:
        mock_confirm.return_value = None
        await procesar_webhook(
            payload_raw=payload,
            signature=None,
            request_id=None,
            sdk=sdk,
            uow=uow,
        )

    mock_confirm.assert_called_once_with(pedido_id=100, uow=uow)
    assert log_entry.procesado is True


@pytest.mark.asyncio
async def test_webhook_firma_invalida():
    """
    Test 12.6 — Invalid signature in production raises HTTP 400.
    """
    pedido = _make_pedido(id=100, usuario_id=10, estado_pedido_id=1)
    log_entry = _make_webhook_log(id=5)
    uow = _make_uow(pedido=pedido, webhook_log=log_entry)
    uow.pago_webhook_logs.create = AsyncMock(return_value=log_entry)

    sdk = _make_sdk()
    payload = {"topic": "payment", "data": {"id": "12345678"}}

    with patch("pagos.service.settings") as mock_settings:
        mock_settings.env = "production"
        mock_settings.mp_access_token = "TEST_TOKEN"

        with pytest.raises(HTTPException) as exc_info:
            await procesar_webhook(
                payload_raw=payload,
                signature="ts=1234567890,v1=invalidsignature",
                request_id="req-123",
                sdk=sdk,
                uow=uow,
            )

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_webhook_idempotente():
    """
    Test 12.7 — Same webhook twice returns 200 without duplicating data.
    Second call finds existing Pago — no duplicate create.
    """
    pedido = _make_pedido(id=100, usuario_id=10, estado_pedido_id=1)
    existing_pago = _make_pago(id=1, mp_payment_id="12345678", mp_status="approved")
    log_entry = _make_webhook_log(id=5)

    # Second call: pago already exists with same mp_id
    uow = _make_uow(pedido=pedido, pago_by_mp_id=existing_pago, webhook_log=log_entry)
    uow.pago_webhook_logs.create = AsyncMock(return_value=log_entry)

    sdk = _make_sdk(
        payment_response={
            "status": 200,
            "response": {
                "id": "12345678",
                "status": "approved",
                "transaction_amount": 1500.0,
                "external_reference": "100",
            },
        }
    )

    payload = {"topic": "payment", "data": {"id": "12345678"}}

    with patch("pedidos.service.confirmar_pedido_por_pago", new_callable=AsyncMock) as mock_confirm:
        # Already confirmed — FSM raises 409
        mock_confirm.side_effect = HTTPException(
            status_code=409, detail={"status": 409}
        )
        # Should NOT raise — 409 from FSM is handled silently
        await procesar_webhook(
            payload_raw=payload,
            signature=None,
            request_id=None,
            sdk=sdk,
            uow=uow,
        )

    # Pago was found — no new create
    uow.pagos.create.assert_not_called()


@pytest.mark.asyncio
async def test_webhook_race_condition():
    """
    Test 12.8 — IntegrityError on Pago.create is handled idempotently.
    The function should not raise, return 200 implicitly.
    """
    pedido = _make_pedido(id=100, usuario_id=10, estado_pedido_id=1)
    log_entry = _make_webhook_log(id=5)
    uow = _make_uow(pedido=pedido, pago_by_mp_id=None, webhook_log=log_entry)
    uow.pago_webhook_logs.create = AsyncMock(return_value=log_entry)

    # First call to get_by_mercadopago_id returns None (not yet created)
    # Then create raises IntegrityError (race condition)
    # Second call to get_by_mercadopago_id returns the existing pago
    existing_pago = _make_pago(id=99, mp_payment_id="12345678", mp_status="approved")
    uow.pagos.get_by_mercadopago_id = AsyncMock(side_effect=[None, existing_pago])
    uow.pagos.create = AsyncMock(
        side_effect=IntegrityError("duplicate", {}, Exception("unique violation"))
    )

    sdk = _make_sdk(
        payment_response={
            "status": 200,
            "response": {
                "id": "12345678",
                "status": "approved",
                "transaction_amount": 1500.0,
                "external_reference": "100",
            },
        }
    )

    payload = {"topic": "payment", "data": {"id": "12345678"}}

    with patch("pedidos.service.confirmar_pedido_por_pago", new_callable=AsyncMock) as mock_confirm:
        mock_confirm.return_value = None
        # Should NOT raise — IntegrityError is handled
        await procesar_webhook(
            payload_raw=payload,
            signature=None,
            request_id=None,
            sdk=sdk,
            uow=uow,
        )


# ---------------------------------------------------------------------------
# Tests for get_pago_status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_pago_status_exitoso():
    """Test 12.9 — CLIENT gets status of their own payment."""
    pedido = _make_pedido(id=100, usuario_id=10, estado_pedido_id=2, total=Decimal("1500.00"))
    pago = _make_pago(
        id=1,
        pedido_id=100,
        mp_payment_id="12345678",
        mp_status="approved",
        preference_id="pref_123",
        monto=Decimal("1500.00"),
    )
    uow = _make_uow(pedido=pedido, pago=pago)

    result = await get_pago_status(
        pedido_id=100,
        usuario_id=10,
        es_admin=False,
        uow=uow,
    )

    assert result.pago_id == 1
    assert result.pedido_id == 100
    assert result.estado == "approved"
    assert result.mercadopago_id == "12345678"


@pytest.mark.asyncio
async def test_get_pago_status_ajeno_forbidden():
    """Test 12.10 — CLIENT cannot access another user's payment status."""
    pedido = _make_pedido(id=100, usuario_id=99, estado_pedido_id=1)
    pago = _make_pago(id=1, pedido_id=100)
    uow = _make_uow(pedido=pedido, pago=pago)

    with pytest.raises(HTTPException) as exc_info:
        await get_pago_status(
            pedido_id=100,
            usuario_id=10,  # different from pedido.usuario_id=99
            es_admin=False,
            uow=uow,
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_pago_status_admin_can_access_any():
    """Admin can access any user's payment status."""
    pedido = _make_pedido(id=100, usuario_id=99, estado_pedido_id=2, total=Decimal("500.00"))
    pago = _make_pago(id=1, pedido_id=100, mp_status="approved")
    uow = _make_uow(pedido=pedido, pago=pago)

    result = await get_pago_status(
        pedido_id=100,
        usuario_id=1,  # admin user, different from pedido owner
        es_admin=True,
        uow=uow,
    )

    assert result.pago_id == 1


@pytest.mark.asyncio
async def test_get_pago_status_pedido_not_found():
    """404 when pedido does not exist."""
    uow = _make_uow(pedido=None)

    with pytest.raises(HTTPException) as exc_info:
        await get_pago_status(
            pedido_id=999, usuario_id=10, es_admin=False, uow=uow
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_pago_status_pago_not_found():
    """404 when pago does not exist for the pedido."""
    pedido = _make_pedido(id=100, usuario_id=10, estado_pedido_id=1)
    uow = _make_uow(pedido=pedido, pago=None)

    with pytest.raises(HTTPException) as exc_info:
        await get_pago_status(
            pedido_id=100, usuario_id=10, es_admin=False, uow=uow
        )

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Tests for confirmar_pedido_por_pago FSM
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_confirmar_pedido_por_pago_success():
    """Pedido PENDIENTE transitions to CONFIRMADO via system webhook."""
    pedido = _make_pedido(id=100, usuario_id=10, estado_pedido_id=1)
    confirmed_pedido = _make_pedido(id=100, usuario_id=10, estado_pedido_id=2)

    uow = MagicMock()
    uow.session = AsyncMock()
    uow.session.add = MagicMock()
    uow.session.flush = AsyncMock()

    pedidos_repo = AsyncMock()
    pedidos_repo.get_by_id = AsyncMock(return_value=pedido)
    pedidos_repo.update_estado = AsyncMock(return_value=confirmed_pedido)
    uow.pedidos = pedidos_repo

    historial_repo = AsyncMock()
    historial_repo.append = AsyncMock()
    uow.historial_estado_pedido = historial_repo

    # Should not raise
    await confirmar_pedido_por_pago(pedido_id=100, uow=uow)

    pedidos_repo.update_estado.assert_called_once_with(100, 2)
    historial_repo.append.assert_called_once()


@pytest.mark.asyncio
async def test_confirmar_pedido_por_pago_not_pendiente():
    """409 if pedido is not in PENDIENTE state."""
    pedido = _make_pedido(id=100, usuario_id=10, estado_pedido_id=2)  # Already CONFIRMADO

    uow = MagicMock()
    uow.session = AsyncMock()
    pedidos_repo = AsyncMock()
    pedidos_repo.get_by_id = AsyncMock(return_value=pedido)
    uow.pedidos = pedidos_repo

    with pytest.raises(HTTPException) as exc_info:
        await confirmar_pedido_por_pago(pedido_id=100, uow=uow)

    assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# Tests for _validate_mp_signature helper
# ---------------------------------------------------------------------------


def test_validate_mp_signature_no_header():
    """Missing signature header returns False."""
    assert _validate_mp_signature(None, None, None) is False


def test_validate_mp_signature_malformed():
    """Malformed header returns False."""
    assert _validate_mp_signature("not-a-valid-signature", None, None) is False


def test_validate_mp_signature_valid():
    """Valid HMAC-SHA256 signature returns True."""
    import hashlib
    import hmac as hmac_module

    # Construct a valid signature
    ts = "1234567890"
    data_id = "12345678"
    request_id = "req-abc-123"
    secret = "TEST_MP_ACCESS_TOKEN"

    manifest = f"id:{data_id};request-id:{request_id};ts:{ts};"
    expected = hmac_module.new(
        secret.encode("utf-8"),
        manifest.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    signature = f"ts={ts},v1={expected}"

    with patch("pagos.service.settings") as mock_settings:
        mock_settings.mp_access_token = secret
        result = _validate_mp_signature(signature, request_id, data_id)

    assert result is True
