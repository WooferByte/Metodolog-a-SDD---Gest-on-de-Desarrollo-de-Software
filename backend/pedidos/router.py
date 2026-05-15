"""
PedidosRouter — HTTP endpoints for order operations.

Endpoints:
  POST /pedidos/validar  — Pre-checkout cart validation (CLIENT only, read-only).

Authentication & Authorization:
  All endpoints require JWT auth. CLIENT role required for validar.
  Uses require_role() from core.dependencies (same pattern as otros routers).
"""
from fastapi import APIRouter, Depends, status

from core.dependencies import require_role
from core.models import Usuario
from infrastructure.uow import UnitOfWork, get_uow
from pedidos import service
from pedidos.schemas import ValidarCarritoRequest, ValidarCarritoResponse

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.post(
    "/validar",
    response_model=ValidarCarritoResponse,
    status_code=status.HTTP_200_OK,
    summary="Validar carrito pre-checkout",
    description=(
        "Valida el contenido del carrito antes de proceder al checkout. "
        "Verifica: carrito vacío, dirección inexistente (HTTP 422), "
        "stock insuficiente y cambios de precio (HTTP 200 con warnings). "
        "Endpoint read-only — no muta ningún dato."
    ),
    responses={
        200: {"description": "Validación completa (puede incluir warnings de stock/precio)"},
        401: {"description": "No autenticado"},
        403: {"description": "Rol insuficiente (requiere CLIENT)"},
        422: {"description": "Carrito vacío o sin dirección de entrega (RFC 7807)"},
    },
)
async def validar_carrito(
    request: ValidarCarritoRequest,
    current_user: Usuario = Depends(require_role(["CLIENT"])),
    uow: UnitOfWork = Depends(get_uow),
) -> ValidarCarritoResponse:
    """
    Pre-checkout cart validation endpoint.

    Accepts the current cart items (with cart-stored prices) and a
    selected delivery address ID. Returns a structured validation report.

    Hard blocks (HTTP 422):
      - items list is empty
      - user has no active delivery addresses

    Soft warnings (HTTP 200 with non-empty arrays):
      - stock_insuficiente: qty requested > available stock
      - productos_invalidos: product is soft-deleted, unavailable, or not found
      - cambios_de_precio: cart price drifted from current DB price by > 0.01

    Clean validation (HTTP 200 with all empty arrays):
      - All items are available with sufficient stock and matching prices.
    """
    async with uow:
        result = await service.validar_carrito(request, current_user.id, uow)
    return result
