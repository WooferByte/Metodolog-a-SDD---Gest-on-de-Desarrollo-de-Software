/**
 * Skeleton — loading placeholder component.
 *
 * Variants:
 *   text    — rounded rect suitable for text lines (default)
 *   circle  — circular shape for avatars/icons
 *   rect    — rectangular shape for images/cards
 *
 * All variants use animate-pulse and muted background.
 * Accepts className for custom width/height.
 */

import type { HTMLAttributes } from 'react'
import { cn } from '@/shared/lib/utils'

type SkeletonVariant = 'text' | 'circle' | 'rect'

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: SkeletonVariant
}

const variantClasses: Record<SkeletonVariant, string> = {
  text:   'rounded-md h-4 w-full',
  circle: 'rounded-full h-10 w-10',
  rect:   'rounded-lg h-24 w-full',
}

export function Skeleton({ variant = 'text', className, ...props }: SkeletonProps) {
  return (
    <div
      role="status"
      aria-label="Cargando..."
      className={cn(
        'animate-pulse bg-muted',
        variantClasses[variant],
        className,
      )}
      {...props}
    />
  )
}
