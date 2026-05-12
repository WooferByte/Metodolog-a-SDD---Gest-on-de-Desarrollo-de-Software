/**
 * Button — accessible, multi-variant button component.
 *
 * Variants: primary | secondary | outline | ghost | destructive
 * Sizes: sm | md | lg
 * Props: loading (shows spinner + disables), disabled, className
 *
 * Uses cn() from shared/lib/utils for class merging.
 * All colors reference semantic design tokens from @theme.
 */

import type { ButtonHTMLAttributes } from 'react'
import { cn } from '@/shared/lib/utils'

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive'
type ButtonSize = 'sm' | 'md' | 'lg'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'bg-primary text-primary-foreground hover:opacity-90 focus-visible:ring-primary',
  secondary:
    'bg-secondary text-secondary-foreground hover:opacity-90 focus-visible:ring-secondary',
  outline:
    'border border-border bg-transparent text-foreground hover:bg-accent hover:text-accent-foreground focus-visible:ring-ring',
  ghost:
    'bg-transparent text-foreground hover:bg-accent hover:text-accent-foreground focus-visible:ring-ring',
  destructive:
    'bg-destructive text-destructive-foreground hover:opacity-90 focus-visible:ring-destructive',
}

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-sm rounded-md',
  md: 'h-10 px-4 text-sm rounded-lg',
  lg: 'h-12 px-6 text-base rounded-lg',
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  className,
  children,
  ...props
}: ButtonProps) {
  const isDisabled = disabled || loading

  return (
    <button
      disabled={isDisabled}
      aria-busy={loading}
      aria-disabled={isDisabled}
      className={cn(
        // Base
        'inline-flex items-center justify-center gap-2 font-medium',
        'transition-colors duration-150',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
        'disabled:pointer-events-none disabled:opacity-50',
        // Variant + size
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      {...props}
    >
      {loading && (
        <svg
          className="animate-spin h-4 w-4 shrink-0"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
          />
        </svg>
      )}
      {children}
    </button>
  )
}
