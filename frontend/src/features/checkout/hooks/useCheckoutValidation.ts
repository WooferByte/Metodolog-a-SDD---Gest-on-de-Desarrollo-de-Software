/**
 * useCheckoutValidation — TanStack Query v5 mutation hook for pre-checkout
 * cart validation.
 *
 * Design decisions (from design.md D-05):
 *   - Uses useMutation, NOT useQuery. Validation is an imperative action
 *     triggered when the checkout page mounts, NOT a cached resource.
 *   - useQuery would refetch on window focus, causing unexpected modal pop-ups.
 *   - useMutation gives the caller full control over when to fire the request.
 *
 * Usage:
 *   const { mutate, isPending, data, isError } = useCheckoutValidation()
 *   // In CheckoutPage useEffect:
 *   useEffect(() => { mutate() }, [])
 *
 * Payload assembly:
 *   - Cart items come from Zustand cartStore.
 *   - precio_carrito falls back to item.price for backward-compat (D-06).
 *   - productId (string) is cast to number for the backend API.
 *   - direccion_id is always 1 for now (address selection UI is a future change).
 *
 * Error handling:
 *   - Network errors or non-422 HTTP errors show a generic toast via UIStore.
 *   - HTTP 422 (hard block) surfaces as mutation.isError — the component
 *     reads mutation.error to display the modal with the specific message.
 */

import { useMutation } from '@tanstack/react-query'
import { useCartStore } from '@/store/cartStore'
import { useUIStore } from '@/store/uiStore'
import { apiClient } from '@/shared/api/axios'
import type { ValidarCarritoRequest, ValidarCarritoResponse } from '../types'

/**
 * POST /api/v1/pedidos/validar — validate the current cart before checkout.
 *
 * Accepts the cart payload and returns the structured validation report.
 * Throws AxiosError on network failure or non-2xx status.
 */
async function validateCart(
  payload: ValidarCarritoRequest,
): Promise<ValidarCarritoResponse> {
  const { data } = await apiClient.post<ValidarCarritoResponse>(
    '/api/v1/pedidos/validar',
    payload,
  )
  return data
}

/**
 * Assemble the validation request payload from the current Zustand cart state.
 *
 * Maps CartItem fields to the backend API shape:
 *   - productId (string) → producto_id (number)
 *   - precio_carrito ?? price → precio_carrito (frozen price snapshot)
 *   - quantity → cantidad
 *
 * direccion_id is set to 1 as a placeholder until the address-selection UI
 * is implemented in a future change.
 */
function buildPayload(
  items: ReturnType<typeof useCartStore.getState>['items'],
): ValidarCarritoRequest {
  return {
    items: items.map((item) => ({
      producto_id: Number(item.productId),
      cantidad: item.quantity,
      // precio_carrito fallback: backward-compat for localStorage items added
      // before this field was introduced (D-06 from design.md)
      precio_carrito: item.precio_carrito ?? item.price,
    })),
    // TODO: replace with selected address ID when address-selection UI is built
    direccion_id: 1,
  }
}

/**
 * useCheckoutValidation
 *
 * Returns TanStack Query v5 mutation object with:
 *   - mutate(): call to trigger the validation. Call once on checkout mount.
 *   - isPending: true while the request is in flight (show spinner/skeleton).
 *   - data: ValidarCarritoResponse on success.
 *   - isError: true on network or HTTP error.
 */
export function useCheckoutValidation() {
  const items = useCartStore((state) => state.items)
  const addToast = useUIStore((state) => state.addToast)

  const mutation = useMutation<ValidarCarritoResponse, Error>({
    mutationFn: () => validateCart(buildPayload(items)),
    onError: (_error) => {
      // 8.4 — Show generic error toast for network errors or unexpected failures.
      // HTTP 422 (hard block) is also caught here — the component inspects
      // mutation.isError and mutation.error for structured display.
      addToast({
        message: 'Error de red al validar el carrito. Intentá nuevamente.',
        type: 'error',
      })
    },
  })

  // 8.5 — Expose a clean interface matching the task spec
  return {
    mutate: mutation.mutate,
    isPending: mutation.isPending,
    data: mutation.data,
    isError: mutation.isError,
  }
}
