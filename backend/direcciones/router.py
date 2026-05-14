"""
DireccionRouter — HTTP endpoints for delivery address CRUD.

All endpoints require JWT authentication (get_current_user dependency).
Ownership is enforced in the service layer (RN-DI03).

Endpoints:
  POST   /direcciones                    → create (201)
  GET    /direcciones                    → list authenticated user's addresses (200)
  GET    /direcciones/{id}               → get one (200)
  PUT    /direcciones/{id}               → full/partial update (200)
  PATCH  /direcciones/{id}/predeterminada → mark as predeterminada (200)
  DELETE /direcciones/{id}               → soft delete (204)
"""
from fastapi import APIRouter, Depends, Response, status

from core.dependencies import get_current_user
from core.models import Usuario
from direcciones import service
from direcciones.schemas import DireccionCreate, DireccionResponse, DireccionUpdate
from infrastructure.uow import UnitOfWork, get_uow

router = APIRouter(prefix="/direcciones", tags=["Direcciones"])


@router.post(
    "",
    response_model=DireccionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear dirección de entrega",
    description=(
        "Crea una nueva dirección para el usuario autenticado. "
        "Si es la primera dirección, se marca como predeterminada automáticamente (RN-DI01)."
    ),
)
async def create_direccion(
    data: DireccionCreate,
    current_user: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> DireccionResponse:
    """Create a new delivery address for the authenticated user."""
    async with uow:
        result = await service.create_direccion(uow, data, current_user.id)
    return DireccionResponse.model_validate(result)


@router.get(
    "",
    response_model=list[DireccionResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar direcciones de entrega",
    description="Retorna todas las direcciones activas del usuario autenticado.",
)
async def list_direcciones(
    current_user: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[DireccionResponse]:
    """Return all active addresses for the authenticated user."""
    async with uow:
        results = await service.list_direcciones(uow, current_user.id)
    return [DireccionResponse.model_validate(d) for d in results]


@router.get(
    "/{id}",
    response_model=DireccionResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener dirección de entrega",
    description="Retorna una dirección específica del usuario autenticado (404 si no existe o no es suya).",
)
async def get_direccion(
    id: int,
    current_user: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> DireccionResponse:
    """Return a single address by ID (ownership enforced)."""
    async with uow:
        result = await service.get_direccion(uow, id, current_user.id)
    return DireccionResponse.model_validate(result)


@router.put(
    "/{id}",
    response_model=DireccionResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar dirección de entrega",
    description="Actualiza los campos de una dirección del usuario autenticado.",
)
async def update_direccion(
    id: int,
    data: DireccionUpdate,
    current_user: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> DireccionResponse:
    """Partially update a delivery address (ownership enforced)."""
    async with uow:
        result = await service.update_direccion(uow, id, data, current_user.id)
    return DireccionResponse.model_validate(result)


@router.patch(
    "/{id}/predeterminada",
    response_model=DireccionResponse,
    status_code=status.HTTP_200_OK,
    summary="Marcar como predeterminada",
    description=(
        "Marca una dirección como predeterminada y desmarca las demás del usuario (RN-DI02)."
    ),
)
async def set_predeterminada(
    id: int,
    current_user: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> DireccionResponse:
    """Mark an address as predeterminada, unsetting all others (RN-DI02)."""
    async with uow:
        result = await service.set_predeterminada(uow, id, current_user.id)
    return DireccionResponse.model_validate(result)


@router.delete(
    "/{id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar dirección de entrega",
    description=(
        "Soft-delete de una dirección del usuario autenticado. "
        "Si era la predeterminada, se reasigna a la más reciente activa."
    ),
)
async def delete_direccion(
    id: int,
    current_user: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    """Soft-delete a delivery address (ownership enforced)."""
    async with uow:
        await service.delete_direccion(uow, id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
