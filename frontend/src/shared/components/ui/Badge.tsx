/**
 * Badge — small status indicator component.
 *
 * Variants:
 *   default     — neutral (uses primary token)
 *   success     — green (uses success token)
 *   warning     — yellow/amber (uses warning token)
 *   error       — red (uses destructive token)
 *   info        — blue (uses info token)
 *
 * Uses semantic tokens from @theme for all colors.
 */

import type { HTMLAttributes } from 'react'
import { cn } from '@/shared/lib/utils'

type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info'

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
}

const variantClasses: Record<BadgeVariant, string> = {
  default: 'bg-primary text-primary-foreground',
  success: 'bg-success text-success-foreground',
  warning: 'bg-warning text-warning-foreground',
  error:   'bg-destructive text-destructive-foreground',
  info:    'bg-info text-info-foreground',
}

export function Badge({ variant = 'default', className, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5',
        'text-xs font-semibold',
        variantClasses[variant],
        className,
      )}
      {...props}
    />
  )
}
