"""
Unit tests for the direcciones module.

Strategy:
  - Service tests: mock UnitOfWork and DireccionRepository with AsyncMock.
    Tests verify business logic (RN-DI01, RN-DI02, RN-DI03, soft-delete
    reassignment) without hitting a real database.
  - Router integration tests: use FastAPI TestClient + dependency_overrides to
    verify auth requirements (401 without token).
"""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

# Ensure backend/ is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_direccion(
    id: int = 1,
    usuario_id: int = 10,
    es_predeterminada: bool = False,
    eliminado_en=None,
) -> MagicMock:
    """Return a MagicMock that behaves like a DireccionEntrega instance."""
    d = MagicMock()
    d.id = id
    d.usuario_id = usuario_id
    d.alias = "Casa"
    d.linea1 = "Av. Corrientes 1234"
    d.piso = None
    d.departamento = None
    d.ciudad = "Buenos Aires"
    d.codigo_postal = "1043"
    d.referencia = None
    d.es_predeterminada = es_predeterminada
    d.creado_en = datetime(2026, 1, 1)
    d.actualizado_en = datetime(2026, 1, 1)
    d.eliminado_en = eliminado_en
    return d


def _make_uow(repo: MagicMock | None = None) -> MagicMock:
    """
    Return a mock UnitOfWork with async context manager support.

    Wires ``async with uow:`` to return the uow itself without a real DB.
    """
    uow = MagicMock()
    if repo is None:
        repo = MagicMock()
    uow.direcciones = repo
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)
    return uow


# ---------------------------------------------------------------------------
# Test 1: create_direccion — primera dirección → predeterminada automática
# ---------------------------------------------------------------------------


class TestCreateDireccionPrimera:
    """RN-DI01: first address auto-gets es_predeterminada=True."""

    @pytest.mark.asyncio
    async def test_primera_direccion_es_predeterminada(self):
        from direcciones.service import create_direccion
        from direcciones.schemas import DireccionCreate

        repo = MagicMock()
        repo.count_active_by_usuario = AsyncMock(return_value=0)
        repo.unset_predeterminada_for_usuario = AsyncMock()
        created = _make_direccion(id=1, usuario_id=10, es_predeterminada=True)
        repo.create = AsyncMock(return_value=created)
        uow = _make_uow(repo)

        data = DireccionCreate(
            alias="Casa",
            linea1="Av. Corrientes 1234",
            ciudad="Buenos Aires",
            codigo_postal="1043",
            es_predeterminada=False,  # user sent False, but must be overridden
        )
        result = await create_direccion(uow, data, usuario_id=10)

        # unset should NOT be called (count was 0, first address)
        repo.unset_predeterminada_for_usuario.assert_not_awaited()
        # create should be called with es_predeterminada forced to True
        call_kwargs = repo.create.call_args[0][0]
        assert call_kwargs.es_predeterminada is True


# ---------------------------------------------------------------------------
# Test 2: create_direccion — segunda dirección, es_predeterminada=False
# ---------------------------------------------------------------------------


class TestCreateDireccionSegundaNoDefault:
    """Second address with es_predeterminada=False → no unset called."""

    @pytest.mark.asyncio
    async def test_segunda_direccion_no_predeterminada(self):
        from direcciones.service import create_direccion
        from direcciones.schemas import DireccionCreate

        repo = MagicMock()
        repo.count_active_by_usuario = AsyncMock(return_value=1)
        repo.unset_predeterminada_for_usuario = AsyncMock()
        created = _make_direccion(id=2, usuario_id=10, es_predeterminada=False)
        repo.create = AsyncMock(return_value=created)
        uow = _make_uow(repo)

        data = DireccionCreate(
            alias="Trabajo",
            linea1="Florida 500",
            ciudad="Buenos Aires",
            codigo_postal="1005",
            es_predeterminada=False,
        )
        await create_direccion(uow, data, usuario_id=10)

        repo.unset_predeterminada_for_usuario.assert_not_awaited()


# ---------------------------------------------------------------------------
# Test 3: create_direccion — segunda dirección, es_predeterminada=True → unset llamado
# ---------------------------------------------------------------------------


class TestCreateDireccionSegundaDefault:
    """RN-DI02: second address with es_predeterminada=True → unset called."""

    @pytest.mark.asyncio
    async def test_segunda_direccion_predeterminada_llama_unset(self):
        from direcciones.service import create_direccion
        from direcciones.schemas import DireccionCreate

        repo = MagicMock()
        repo.count_active_by_usuario = AsyncMock(return_value=1)
        repo.unset_predeterminada_for_usuario = AsyncMock()
        created = _make_direccion(id=2, usuario_id=10, es_predeterminada=True)
        repo.create = AsyncMock(return_value=created)
        uow = _make_uow(repo)

        data = DireccionCreate(
            alias="Trabajo",
            linea1="Florida 500",
            ciudad="Buenos Aires",
            codigo_postal="1005",
            es_predeterminada=True,
        )
        await create_direccion(uow, data, usuario_id=10)

        repo.unset_predeterminada_for_usuario.assert_awaited_once_with(10)


# ---------------------------------------------------------------------------
# Test 4: list_direcciones — retorna lista del usuario
# ---------------------------------------------------------------------------


class TestListDirecciones:
    """list_direcciones delegates to repository and returns results unchanged."""

    @pytest.mark.asyncio
    async def test_list_returns_user_addresses(self):
        from direcciones.service import list_direcciones

        addresses = [_make_direccion(1, 10), _make_direccion(2, 10)]
        repo = MagicMock()
        repo.list_by_usuario = AsyncMock(return_value=addresses)
        uow = _make_uow(repo)

        result = await list_direcciones(uow, usuario_id=10)

        assert result == addresses
        repo.list_by_usuario.assert_awaited_once_with(10)


# ---------------------------------------------------------------------------
# Test 5: get_direccion — ID existe y es del usuario
# ---------------------------------------------------------------------------


class TestGetDireccionFound:
    """get_direccion returns address when found and owned by user."""

    @pytest.mark.asyncio
    async def test_get_direccion_found(self):
        from direcciones.service import get_direccion

        addr = _make_direccion(id=5, usuario_id=10)
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=addr)
        uow = _make_uow(repo)

        result = await get_direccion(uow, direccion_id=5, usuario_id=10)

        assert result is addr


# ---------------------------------------------------------------------------
# Test 6: get_direccion — ID no existe → 404
# ---------------------------------------------------------------------------


class TestGetDireccionNotFound:
    """get_direccion raises 404 when address does not exist."""

    @pytest.mark.asyncio
    async def test_get_direccion_not_found(self):
        from direcciones.service import get_direccion

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)
        uow = _make_uow(repo)

        with pytest.raises(HTTPException) as exc_info:
            await get_direccion(uow, direccion_id=999, usuario_id=10)

        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Test 7: get_direccion — ID de otro usuario → 404 (RN-DI03)
# ---------------------------------------------------------------------------


class TestGetDireccionWrongUser:
    """RN-DI03: address belonging to another user returns 404 (not 403)."""

    @pytest.mark.asyncio
    async def test_get_direccion_other_user_returns_404(self):
        from direcciones.service import get_direccion

        addr = _make_direccion(id=5, usuario_id=99)  # belongs to user 99
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=addr)
        uow = _make_uow(repo)

        with pytest.raises(HTTPException) as exc_info:
            await get_direccion(uow, direccion_id=5, usuario_id=10)  # requesting as user 10

        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Test 8: update_direccion — update parcial exitoso
# ---------------------------------------------------------------------------


class TestUpdateDireccionParcial:
    """update_direccion applies only non-None fields."""

    @pytest.mark.asyncio
    async def test_update_only_alias(self):
        from direcciones.service import update_direccion
        from direcciones.schemas import DireccionUpdate

        addr = _make_direccion(id=1, usuario_id=10)
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=addr)
        repo.unset_predeterminada_for_usuario = AsyncMock()
        repo.update = AsyncMock(return_value=addr)
        uow = _make_uow(repo)

        data = DireccionUpdate(alias="Nuevo Alias")
        await update_direccion(uow, direccion_id=1, data=data, usuario_id=10)

        # Only alias should be set; no unset called (es_predeterminada not in payload)
        assert addr.alias == "Nuevo Alias"
        repo.unset_predeterminada_for_usuario.assert_not_awaited()
        repo.update.assert_awaited_once_with(addr)


# ---------------------------------------------------------------------------
# Test 9: update_direccion — de otro usuario → 404
# ---------------------------------------------------------------------------


class TestUpdateDireccionWrongUser:
    """update_direccion raises 404 for addresses owned by another user."""

    @pytest.mark.asyncio
    async def test_update_other_user_404(self):
        from direcciones.service import update_direccion
        from direcciones.schemas import DireccionUpdate

        addr = _make_direccion(id=1, usuario_id=99)
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=addr)
        uow = _make_uow(repo)

        with pytest.raises(HTTPException) as exc_info:
            await update_direccion(uow, 1, DireccionUpdate(alias="x"), usuario_id=10)

        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Test 10: set_predeterminada — llama unset y setea True (RN-DI02)
# ---------------------------------------------------------------------------


class TestSetPredeterminada:
    """RN-DI02: set_predeterminada unsets others and marks target."""

    @pytest.mark.asyncio
    async def test_set_predeterminada_calls_unset_and_sets_true(self):
        from direcciones.service import set_predeterminada

        addr = _make_direccion(id=3, usuario_id=10, es_predeterminada=False)
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=addr)
        repo.unset_predeterminada_for_usuario = AsyncMock()
        repo.update = AsyncMock(return_value=addr)
        uow = _make_uow(repo)

        result = await set_predeterminada(uow, direccion_id=3, usuario_id=10)

        repo.unset_predeterminada_for_usuario.assert_awaited_once_with(10)
        assert addr.es_predeterminada is True
        repo.update.assert_awaited_once_with(addr)


# ---------------------------------------------------------------------------
# Test 11: set_predeterminada — de otro usuario → 404
# ---------------------------------------------------------------------------


class TestSetPredeterminadaWrongUser:
    """set_predeterminada raises 404 for addresses owned by another user."""

    @pytest.mark.asyncio
    async def test_set_predeterminada_other_user_404(self):
        from direcciones.service import set_predeterminada

        addr = _make_direccion(id=3, usuario_id=99)
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=addr)
        uow = _make_uow(repo)

        with pytest.raises(HTTPException) as exc_info:
            await set_predeterminada(uow, direccion_id=3, usuario_id=10)

        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Test 12: delete_direccion — no predeterminada → soft_delete sin reasignación
# ---------------------------------------------------------------------------


class TestDeleteDireccionNoPredeterminada:
    """Soft-delete of a non-predeterminada address: no reassignment."""

    @pytest.mark.asyncio
    async def test_delete_no_predeterminada_no_reassign(self):
        from direcciones.service import delete_direccion

        addr = _make_direccion(id=1, usuario_id=10, es_predeterminada=False)
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=addr)
        repo.soft_delete = AsyncMock()
        repo.get_latest_active_by_usuario = AsyncMock()
        uow = _make_uow(repo)

        await delete_direccion(uow, direccion_id=1, usuario_id=10)

        repo.soft_delete.assert_awaited_once_with(1)
        repo.get_latest_active_by_usuario.assert_not_awaited()


# ---------------------------------------------------------------------------
# Test 13: delete_direccion — era predeterminada, hay siguiente → reasigna
# ---------------------------------------------------------------------------


class TestDeleteDireccionEraDefaultConSiguiente:
    """Soft-delete of predeterminada address: reassigns to next active."""

    @pytest.mark.asyncio
    async def test_delete_predeterminada_reassigns_to_next(self):
        from direcciones.service import delete_direccion

        addr = _make_direccion(id=1, usuario_id=10, es_predeterminada=True)
        siguiente = _make_direccion(id=2, usuario_id=10, es_predeterminada=False)

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=addr)
        repo.soft_delete = AsyncMock()
        repo.get_latest_active_by_usuario = AsyncMock(return_value=siguiente)
        repo.update = AsyncMock(return_value=siguiente)
        uow = _make_uow(repo)

        await delete_direccion(uow, direccion_id=1, usuario_id=10)

        repo.soft_delete.assert_awaited_once_with(1)
        repo.get_latest_active_by_usuario.assert_awaited_once_with(10)
        assert siguiente.es_predeterminada is True
        repo.update.assert_awaited_once_with(siguiente)


# ---------------------------------------------------------------------------
# Test 14: delete_direccion — era predeterminada, no hay más → sin reasignación
# ---------------------------------------------------------------------------


class TestDeleteDireccionEraDefaultSinSiguiente:
    """Soft-delete of predeterminada address with no remaining addresses."""

    @pytest.mark.asyncio
    async def test_delete_predeterminada_no_siguiente_no_update(self):
        from direcciones.service import delete_direccion

        addr = _make_direccion(id=1, usuario_id=10, es_predeterminada=True)

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=addr)
        repo.soft_delete = AsyncMock()
        repo.get_latest_active_by_usuario = AsyncMock(return_value=None)
        repo.update = AsyncMock()
        uow = _make_uow(repo)

        await delete_direccion(uow, direccion_id=1, usuario_id=10)

        repo.soft_delete.assert_awaited_once_with(1)
        repo.get_latest_active_by_usuario.assert_awaited_once_with(10)
        repo.update.assert_not_awaited()


# ---------------------------------------------------------------------------
# Router integration tests (Tests 15–17) — auth requirements
# ---------------------------------------------------------------------------


def _get_test_client() -> TestClient:
    """Build a TestClient for the full FastAPI app."""
    from main import app
    return TestClient(app, raise_server_exceptions=False)


class TestRouterAuthRequired:
    """All direcciones endpoints require JWT authentication (401 without token)."""

    def test_post_direcciones_sin_token_retorna_401(self):
        client = _get_test_client()
        resp = client.post(
            "/api/v1/direcciones",
            json={
                "alias": "Casa",
                "linea1": "Av. Corrientes 1234",
                "ciudad": "Buenos Aires",
                "codigo_postal": "1043",
            },
        )
        assert resp.status_code == 401

    def test_get_direcciones_sin_token_retorna_401(self):
        client = _get_test_client()
        resp = client.get("/api/v1/direcciones")
        assert resp.status_code == 401

    def test_delete_direccion_sin_token_retorna_401(self):
        client = _get_test_client()
        resp = client.delete("/api/v1/direcciones/1")
        assert resp.status_code == 401
