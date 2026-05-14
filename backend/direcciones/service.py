"""
DireccionService — business logic for delivery address CRUD.

Rules enforced:
  RN-DI01: First address for a user is automatically set as predeterminada.
  RN-DI02: Only one address per user can be predeterminada at a time.
  RN-DI03: Users can only access their own addresses (ownership check → 404).

Architecture note:
  - Never calls session.commit() — the UoW context manager handles that.
  - Only this layer raises HTTPException (never the router or repository).
"""
from fastapi import HTTPException, status

from core.models import DireccionEntrega
from direcciones.schemas import DireccionCreate, DireccionUpdate


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


async def _get_or_404(uow, direccion_id: int, usuario_id: int) -> DireccionEntrega:
    """
    Load an address by ID and verify it belongs to the requesting user.

    Per RN-DI03 the same 404 is returned whether the address doesn't exist
    OR belongs to another user — this avoids leaking existence information.

    Args:
        uow: Active UnitOfWork instance.
        direccion_id: Primary key of the address to load.
        usuario_id: ID of the authenticated user.

    Returns:
        DireccionEntrega if it exists and belongs to the user.

    Raises:
        HTTPException 404 if not found or not owned by user.
    """
    direccion: DireccionEntrega | None = await uow.direcciones.get_by_id(direccion_id)
    if direccion is None or direccion.usuario_id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Not Found",
                "status": 404,
                "detail": "Dirección no encontrada",
            },
        )
    return direccion


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def list_direcciones(uow, usuario_id: int) -> list[DireccionEntrega]:
    """
    Return all active delivery addresses for the authenticated user.

    Args:
        uow: Active UnitOfWork instance.
        usuario_id: ID of the authenticated user.

    Returns:
        List of DireccionEntrega (may be empty).
    """
    return await uow.direcciones.list_by_usuario(usuario_id)


async def get_direccion(
    uow, direccion_id: int, usuario_id: int
) -> DireccionEntrega:
    """
    Return a single delivery address (ownership enforced).

    Args:
        uow: Active UnitOfWork instance.
        direccion_id: Primary key of the address.
        usuario_id: ID of the authenticated user.

    Returns:
        DireccionEntrega if found and owned by user.

    Raises:
        HTTPException 404 if not found or not owned.
    """
    return await _get_or_404(uow, direccion_id, usuario_id)


async def create_direccion(
    uow, data: DireccionCreate, usuario_id: int
) -> DireccionEntrega:
    """
    Create a new delivery address for the authenticated user.

    RN-DI01: If this is the user's first address, force es_predeterminada=True.
    RN-DI02: If es_predeterminada=True and user already has addresses,
             unset all existing predeterminada flags before creating.

    Args:
        uow: Active UnitOfWork instance.
        data: Validated creation payload.
        usuario_id: ID of the authenticated user.

    Returns:
        Created DireccionEntrega.
    """
    count = await uow.direcciones.count_active_by_usuario(usuario_id)

    # Build mutable dict from schema
    address_data = data.model_dump()

    if count == 0:
        # RN-DI01: first address is always predeterminada
        address_data["es_predeterminada"] = True
    elif address_data.get("es_predeterminada"):
        # RN-DI02: unset existing predeterminada before setting new one
        await uow.direcciones.unset_predeterminada_for_usuario(usuario_id)

    direccion = DireccionEntrega(**address_data, usuario_id=usuario_id)
    return await uow.direcciones.create(direccion)


async def update_direccion(
    uow, direccion_id: int, data: DireccionUpdate, usuario_id: int
) -> DireccionEntrega:
    """
    Partially update a delivery address (ownership enforced).

    RN-DI02: If es_predeterminada=True in payload, unset existing flags first.

    Args:
        uow: Active UnitOfWork instance.
        direccion_id: Primary key of the address to update.
        data: Validated partial-update payload.
        usuario_id: ID of the authenticated user.

    Returns:
        Updated DireccionEntrega.

    Raises:
        HTTPException 404 if not found or not owned.
    """
    direccion = await _get_or_404(uow, direccion_id, usuario_id)

    update_data = data.model_dump(exclude_none=True)

    if update_data.get("es_predeterminada") is True:
        # RN-DI02
        await uow.direcciones.unset_predeterminada_for_usuario(usuario_id)

    for field, value in update_data.items():
        setattr(direccion, field, value)

    return await uow.direcciones.update(direccion)


async def set_predeterminada(
    uow, direccion_id: int, usuario_id: int
) -> DireccionEntrega:
    """
    Mark a delivery address as predeterminada.

    RN-DI02: Unsets all other predeterminada flags for the user first.

    Args:
        uow: Active UnitOfWork instance.
        direccion_id: Primary key of the address to mark.
        usuario_id: ID of the authenticated user.

    Returns:
        Updated DireccionEntrega with es_predeterminada=True.

    Raises:
        HTTPException 404 if not found or not owned.
    """
    direccion = await _get_or_404(uow, direccion_id, usuario_id)

    # RN-DI02: unset all existing predeterminada flags
    await uow.direcciones.unset_predeterminada_for_usuario(usuario_id)

    direccion.es_predeterminada = True
    return await uow.direcciones.update(direccion)


async def delete_direccion(uow, direccion_id: int, usuario_id: int) -> None:
    """
    Soft-delete a delivery address (ownership enforced).

    If the deleted address was predeterminada, reassign predeterminada to
    the most recently created active address for the user (if any).

    Args:
        uow: Active UnitOfWork instance.
        direccion_id: Primary key of the address to delete.
        usuario_id: ID of the authenticated user.

    Raises:
        HTTPException 404 if not found or not owned.
    """
    direccion = await _get_or_404(uow, direccion_id, usuario_id)
    era_predeterminada = direccion.es_predeterminada

    await uow.direcciones.soft_delete(direccion_id)

    if era_predeterminada:
        siguiente = await uow.direcciones.get_latest_active_by_usuario(usuario_id)
        if siguiente is not None:
            siguiente.es_predeterminada = True
            await uow.direcciones.update(siguiente)
