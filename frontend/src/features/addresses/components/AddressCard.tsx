/**
 * AddressCard — displays a single address with action buttons.
 *
 * Features:
 *   - Badge "Predeterminada" shown only when es_predeterminada === true
 *   - "Editar" button always visible
 *   - "Eliminar" button always visible
 *   - "Marcar predeterminada" button hidden when already default
 *
 * Tokens: only semantic @theme tokens — no raw Tailwind colors.
 * ARIA: article with aria-label, descriptive aria-labels on buttons.
 */

import { Badge } from '@/shared/components/ui/Badge'
import { Button } from '@/shared/components/ui/Button'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from '@/shared/components/ui/Card'
import type { DireccionResponse } from '@/features/addresses/types'

export interface AddressCardProps {
  address: DireccionResponse
  onEdit: () => void
  onDelete: () => void
  onSetPredeterminada: () => void
  isPending?: boolean
}

export function AddressCard({
  address,
  onEdit,
  onDelete,
  onSetPredeterminada,
  isPending = false,
}: AddressCardProps) {
  const {
    alias,
    linea1,
    piso,
    departamento,
    ciudad,
    codigo_postal,
    referencia,
    es_predeterminada,
  } = address

  const secondLine = [piso && `Piso ${piso}`, departamento && `Dpto. ${departamento}`]
    .filter(Boolean)
    .join(', ')

  return (
    <article aria-label={alias}>
      <Card className="h-full flex flex-col">
        <CardHeader className="p-4 pb-2">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-base">{alias}</CardTitle>
            {es_predeterminada && (
              <Badge variant="success" className="shrink-0">
                Predeterminada
              </Badge>
            )}
          </div>
        </CardHeader>

        <CardContent className="p-4 pt-0 flex-1 flex flex-col gap-0.5 text-sm text-muted-foreground">
          <p>{linea1}</p>
          {secondLine && <p>{secondLine}</p>}
          <p>
            {ciudad}, {codigo_postal}
          </p>
          {referencia && (
            <p className="text-xs text-muted-foreground mt-1">Ref: {referencia}</p>
          )}
        </CardContent>

        <CardFooter className="p-4 pt-0 flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onEdit}
            aria-label={`Editar dirección ${alias}`}
            disabled={isPending}
          >
            Editar
          </Button>

          {!es_predeterminada && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onSetPredeterminada}
              aria-label={`Marcar ${alias} como predeterminada`}
              disabled={isPending}
            >
              Predeterminada
            </Button>
          )}

          <Button
            variant="destructive"
            size="sm"
            onClick={onDelete}
            aria-label={`Eliminar dirección ${alias}`}
            disabled={isPending}
          >
            Eliminar
          </Button>
        </CardFooter>
      </Card>
    </article>
  )
}
