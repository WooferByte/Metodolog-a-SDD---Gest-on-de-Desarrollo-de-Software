/**
 * DeleteAddressDialog — confirmation modal before deleting an address.
 *
 * Shows the address alias to confirm the user is deleting the right entry.
 * Buttons: "Cancelar" (safe, closes) and "Eliminar" (destructive, confirms).
 *
 * Tokens: only semantic @theme tokens — no raw Tailwind colors.
 */

import { Modal } from '@/shared/components/ui/Modal'
import { Button } from '@/shared/components/ui/Button'

export interface DeleteAddressDialogProps {
  isOpen: boolean
  alias: string
  onCancel: () => void
  onConfirm: () => void
  isPending?: boolean
}

export function DeleteAddressDialog({
  isOpen,
  alias,
  onCancel,
  onConfirm,
  isPending = false,
}: DeleteAddressDialogProps) {
  return (
    <Modal isOpen={isOpen} onClose={onCancel} title="Eliminar dirección">
      <div className="flex flex-col gap-6">
        <p className="text-sm text-muted-foreground">
          ¿Eliminás la dirección{' '}
          <span className="font-semibold text-foreground">{alias}</span>? Esta acción
          no se puede deshacer.
        </p>

        <div className="flex justify-end gap-3">
          <Button
            type="button"
            variant="outline"
            size="md"
            onClick={onCancel}
            disabled={isPending}
          >
            Cancelar
          </Button>

          <Button
            type="button"
            variant="destructive"
            size="md"
            loading={isPending}
            onClick={onConfirm}
            aria-label={`Confirmar eliminación de ${alias}`}
          >
            Eliminar
          </Button>
        </div>
      </div>
    </Modal>
  )
}
