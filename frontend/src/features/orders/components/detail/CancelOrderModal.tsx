/**
 * CancelOrderModal — confirmation dialog for cancelling an order.
 *
 * Uses the shared native <dialog>-based Modal component which provides:
 *   - Built-in focus trap (native <dialog> showModal())
 *   - Escape key closes without executing the mutation
 *   - aria-modal="true" + aria-labelledby automatically
 *   - WCAG SC 2.1.2 compliance (no keyboard trap)
 *
 * State management: modal open/close via useOrderDetailStore (Zustand v5).
 * Mutation: useCancelOrder which handles success toast and cache invalidation.
 */

import { Modal } from '@/shared/components/ui/Modal'
import { Button } from '@/shared/components/ui/Button'
import { useOrderDetailStore } from '@/features/orders/store/orderDetailStore'
import { useCancelOrder } from '@/features/orders/hooks/useCancelOrder'

export interface CancelOrderModalProps {
  orderId: number
}

export function CancelOrderModal({ orderId }: CancelOrderModalProps) {
  const isCancelModalOpen = useOrderDetailStore((state) => state.isCancelModalOpen)
  const closeCancelModal = useOrderDetailStore((state) => state.closeCancelModal)
  const { mutate: cancelOrder, isPending } = useCancelOrder()

  const handleConfirm = () => {
    cancelOrder(orderId)
  }

  return (
    <Modal
      isOpen={isCancelModalOpen}
      onClose={closeCancelModal}
      title="Cancelar pedido"
    >
      <div className="flex flex-col gap-6">
        {/* Description — also provides aria-describedby context via modal's aria-labelledby */}
        <p
          id="cancel-order-description"
          className="text-sm text-muted-foreground"
        >
          ¿Estás seguro de que querés cancelar el pedido{' '}
          <span className="font-mono font-medium text-foreground">
            #{orderId}
          </span>
          ? Esta acción no se puede deshacer. El stock será reintegrado automáticamente.
        </p>

        {/* Action buttons */}
        <div className="flex flex-col gap-2 sm:flex-row-reverse sm:gap-3">
          <Button
            variant="destructive"
            onClick={handleConfirm}
            loading={isPending}
            disabled={isPending}
            aria-label={`Confirmar cancelación del pedido #${orderId}`}
          >
            Sí, cancelar pedido
          </Button>
          <Button
            variant="outline"
            onClick={closeCancelModal}
            disabled={isPending}
            aria-label="No cancelar, mantener pedido"
          >
            No, mantener pedido
          </Button>
        </div>
      </div>
    </Modal>
  )
}
